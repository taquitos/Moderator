"""Chrome Extension Moderation"""
from pathlib import Path
import re
import os
import json
import sys
import stat
import errno
import getpass

if getpass.getuser() == 'root':
    print("🙅‍♂️ Don't execute " + sys.argv[0] + " as root, exiting.")
    sys.exit(1)

# Call this script passing in the name of the extension you wish to moderate.
if len(sys.argv) - 1 != 1:
    print("Error: you must pass the name of the extension you wish to moderate, and only the name")
    print("e.g.: $python3 moderate.py \"Hooli Spy\"")
    sys.exit(1)

EXTENSION_NAME = sys.argv[1]
EXTENSIONS_ROOT_FOLDER = '/Library/Application Support/Google/Chrome/Default/Extensions'
EXTENSIONS_FOLDER = os.path.expanduser('~') + EXTENSIONS_ROOT_FOLDER
TARGET_EXTENSION_FOLDER_REGEX = '(('+EXTENSIONS_FOLDER + '/[a-z]+)/.*/)'

def lock_extension_folder(folder):
    """Uses chflags to set user-immutable."""
    print("🔐 Locking the extension folder: " + folder
          + "\n   so it can't be automatically updated in the future.")
    lock_success = False
    try:
        # It's possible one could encounter a permission error here.
        os.chflags(folder, stat.UF_IMMUTABLE)
        lock_success = True
    except IOError as error:
        if (error.errno == errno.EPERM or error.errno == errno.EACCES):
            print("❗️ Encountered an error running: \n   $chflags uchg " + folder)
            print("   Which is setting the `user immutable flag`.")
            print("⭐️ To fix this error, run: $chflags uchg " + folder)
        else:
            print("❗️An unknown error occured:" + str(error.errno))
            sys.exit(1)
    print("✅ Done locking " + folder)
    return lock_success

def clean_file(file_name):
    """Overwrite file we are cleaning with a single console.log() message."""
    print("💅 Moderating " + file_name)
    file_to_clean = open(file_name, "w+")
    file_to_clean.write("console.log(\"No thank you\")\n")
    print("✅ Done moderating " + file_name)

def clean_content_scripts(folder, manifest_json):
    """
    Iterate through all "content" scripts and clean them out.
    Structure is
    "content_scripts": [ {
      "js": [ "<file_name>" ],
    } ],
    """
    print("🔍 Looking for and cleaning defined content scripts in the manifest.")
    cleaned = False
    if manifest_json.get('content_scripts'):
        content_scripts = manifest_json['content_scripts']
        for script in content_scripts:
            if script.get('js'):
                script_files = script['js']
                for script_file in script_files:
                    clean_file(folder + script_file)
                    cleaned = True
    if not cleaned:
        print("🤷‍♂️ No content scripts found in the manifest.")
    else:
        print("✅ Done moderating content scripts")

def clean_background_scripts(folder, manifest_json):
    """
    Iterate through all "background" scripts and clean them out.

    Structure is
    "background": {
      "scripts": [ "<file_name>" ]
    },
    """
    print("🔍 Looking for and cleaning defined background scripts in the manifest.")
    cleaned = False
    if manifest_json.get('background'):
        content_scripts = manifest_json['background'].get('scripts')
        for script_file in content_scripts:
            clean_file(folder + script_file)
            cleaned = True
    if not cleaned:
        print("🤷‍♂️ No background scripts found in the manifest.")
    else:
        print("✅ Done moderating background scripts")

def clean_web_accessible_resource_scripts(folder, manifest_json):
    """
    Iterate through all "web_accessible_resources" scripts and clean them out.

    Structure is
     "web_accessible_resources": [ "page_embed_script.js" ]
    """
    print("🔍 Looking for and cleaning defined background scripts in the manifest.")
    cleaned = False
    if manifest_json.get('web_accessible_resources'):
        content_scripts = manifest_json['web_accessible_resources']
        for script_file in content_scripts:
            clean_file(folder + script_file)
            cleaned = True
    if not cleaned:
        print("🤷‍♂️ No web accessible resource scripts found in the manifest.")
    else:
        print("✅ Done moderating web accessible resource scripts")

def get_name_from_messages(name_key, extension_folder):
    """
    Sometimes the name isn't in the manifest, but it's a key to a message in the messages.json.
    This is because extensions can be localized, so the app name is stored as a message.
    """
    # Strip off __MSG_ in the front, and __ at the end
    message_name_key = name_key[6:-2]
    for file_name in Path(extension_folder).rglob('messages.json'):
    # Parse the messages looking for the `appname` attribute so we can match on it.
        with open(file_name, 'r') as file:
            messages_json_string = file.read().replace('\n', '')
            parsed_messages_json = json.loads(messages_json_string.encode().decode('utf-8-sig'))
            if parsed_messages_json.get(message_name_key):
                app_name = parsed_messages_json[message_name_key]['message']
                if app_name.lower() == EXTENSION_NAME.lower():
                    return True
            # Sometimes case doesn't match, so try looking for all lower-case.
            # Really, though, we should probably just map the keys to lower before we start.
            elif parsed_messages_json.get(message_name_key.lower()):
                app_name = parsed_messages_json[message_name_key.lower()]['message']
                if app_name.lower() == EXTENSION_NAME.lower():
                    return True
    return False

def handle_matched_extension(file_name, parsed_manifest):
    """Once an extension is found to be a match, execute the steps to moderate it."""
    print("🔍 Found extension \"" + EXTENSION_NAME + "\" in " + EXTENSIONS_FOLDER)
    match = re.search(TARGET_EXTENSION_FOLDER_REGEX, str(file_name))
    # Get the root of the extension (looks like "Extensions/dkalehcagomngckvmicbjnlhfjcjbwmq").
    extension_root = match.group(2)
    # Get the root of the current version of the extension
    # (looks like "Extensions/dkalehcagomngckvmicbjnlhfjcjbwmq/0.0.9_0").
    current_extension_version_root = match.group(1)
    # Before we clean, we need to lock the folder so it can't be automatically repaired.
    if lock_extension_folder(extension_root):
        clean_content_scripts(current_extension_version_root, parsed_manifest)
        clean_background_scripts(current_extension_version_root, parsed_manifest)
        clean_web_accessible_resource_scripts(current_extension_version_root, parsed_manifest)
        return True
    return False

def start_moderating():
    """Main driver for the moderation action."""
    print("🙈 Attempting to moderate \"" + EXTENSION_NAME + "\" extension")
    success = False
    found_at_least_one_match = False
    # Iterate through all extension folders looking for the manifest.json
    # so we can find the extension name.
    for filename in Path(EXTENSIONS_FOLDER).rglob('manifest.json'):
        # Parse the messages looking for the `appname` attribute so we can match on it.
        with open(filename, 'r') as manifest_file:
            json_string = manifest_file.read().replace('\n', '')
            # Sometimes the string format contains unicode characters.
            parsed_json = json.loads(json_string.encode().decode('utf-8-sig'))
            if parsed_json.get('name'):
                name = str(parsed_json['name'])
                success = False
                # Often app name is just a key to a message, so we need to look it up in that case.
                if "__MSG_" in name:
                    if get_name_from_messages(name, Path(EXTENSIONS_FOLDER)):
                        found_at_least_one_match = True
                        success = handle_matched_extension(filename, parsed_json)
                elif name.lower() == EXTENSION_NAME.lower():
                    found_at_least_one_match = True
                    success = handle_matched_extension(filename, parsed_json)

    if not found_at_least_one_match:
        print("❗️ No matching extension found for \"" + EXTENSION_NAME + "\"")
        sys.exit(1)

    if not success:
        print("❗️ Moderation completed with one or more errors. " +
              "To see suggested resolutions, look for ⭐️'s in the output")
    else:
        print("✅ Moderation completed 🕺")

if __name__ == "__main__":
    start_moderating()
