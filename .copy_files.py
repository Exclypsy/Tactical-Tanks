

# Skript na kopirvanie viacerych suborov do schranky (PO JEDNOM, lebo inak to neide)
# ------------ PROSIM NECOMMITUJTE ZMENY CIEST Z TOHTO SUBORU!!! -----------------
# xoxo <3

import platform
import subprocess

file_paths = [
    "C:\\Users\\Admin\PycharmProjects\\OPGP-Projekt-MOS-\\server\\Server.py",
    "C:\\Users\\Admin\PycharmProjects\\OPGP-Projekt-MOS-\\client\\Client.py",
    "C:\\Users\\Admin\PycharmProjects\\OPGP-Projekt-MOS-\\Lobby.py"
    # "C:\\Users\\Admin\PycharmProjects\\OPGP-Projekt-MOS-\\client\\game.py",
]



def copy_file_to_clipboard(file_path):
    system = platform.system()

    if system == "Windows":
        # Windows implementation using PowerShell
        powershell_cmd = f'Set-Clipboard -Path "{file_path}"'
        subprocess.run(["powershell", "-Command", powershell_cmd])
        file_name = file_path.split("\\")[-1]
        print(f"Copied to clipboard: {str(file_name).upper()}")

    elif system == "Darwin":  # macOS
        # macOS implementation using AppleScript
        apple_script = f'''
tell application "Finder"
    set the clipboard to (POSIX file "{file_path}" as alias)
end tell
'''
        subprocess.run(["osascript", "-e", apple_script])
        print(f"Copied to clipboard: {file_path}")

    else:
        print("Unsupported operating system")


def main():
    total_files = len(file_paths)

    for i, file_path in enumerate(file_paths):
        print(f"\nFile {i + 1} of {total_files}")
        copy_file_to_clipboard(file_path)

        # Don't ask for input after the last file
        if i < total_files - 1:
            input("Press Enter to copy the next file...")


if __name__ == "__main__":
    main()
