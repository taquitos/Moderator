# Moderator: Permanantly disable auto-installing, auto-repairing, and auto-updating Chrome extensions.
[![Twitter: @taquitos](https://img.shields.io/badge/contact-@taquitos-orange.svg?style=flat)](https://twitter.com/FastlaneTools)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Do you have a Chrome extension that keeps installing and updating itself that you'd rather not have? Time to moderate it!

It's as easy as:
```
python3 moderate.py "Extension Name"
```

And in no time that extension will no longer be working or self-updating/self-repairing. This script locks the specific extension folder so that no automated process can install a new version.

What your extensions look like before:

<img src="https://i.imgur.com/SUxqmg8.png" width="400"/>

Moderate!
![Running moderator commandline](https://i.imgur.com/sUqnLUx.gif "moderator in action!")

After:

<img src="https://i.imgur.com/F3ZJWcL.png" width="400"/>

## How it works
- The script looks for an `Extensions` folder in your `~/Library/Application Support/Google/Chrome/Default` path.
- It iterates through each folder looking for `manifest.json` 
- Determines the current extension's name and checks if it's a match (sometimes requiring a dive into the `messages.json`)
- Once a match is found, it locks the extension root using `chflags` to prevent updates from Chrome.
- Checks the manifest for all associated script files
- Overwrites the contents of each script file with `console.log("No thank you")`

### Note
I'm not a Python programmer, and I didn't spend much time on this so it's most likely trash 🗑

I did test it on a couple computers a few different extensions, though 😁