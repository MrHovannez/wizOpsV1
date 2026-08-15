import base64
import shutil
import subprocess


class Clipboard:
    def copy(self, text: str):
        for cmd, name in [
            (["wl-copy"], "wl-copy"),
            (["xclip", "-selection", "clipboard"], "xclip"),
            (["xsel", "--clipboard", "--input"], "xsel"),
        ]:
            if shutil.which(cmd[0]):
                try:
                    subprocess.run(
                        cmd,
                        input=text,
                        text=True,
                        check=True,
                        timeout=3,
                    )
                    return name
                except Exception:
                    pass

        try:
            payload = base64.b64encode(text.encode("utf-8")).decode("ascii")

            with open("/dev/tty", "w") as tty:
                tty.write(f"\033]52;c;{payload}\a")
                tty.flush()

            return "terminal OSC52"

        except Exception:
            return None
