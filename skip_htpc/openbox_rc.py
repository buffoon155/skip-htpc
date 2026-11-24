from __future__ import annotations

import re

F13_COMMAND = "/usr/local/bin/launch.sh next"

F13_KEYBIND = f"""    <keybind key="F13">
      <action name="Execute">
        <command>{F13_COMMAND}</command>
      </action>
    </keybind>
"""

APP_RULES = """    <application class="skip-htpc-netflix">
      <maximized>yes</maximized>
      <focus>yes</focus>
    </application>
    <application class="skip-htpc-areena">
      <maximized>yes</maximized>
      <focus>yes</focus>
    </application>
"""


def ensure_cycle_keybind(xml_text: str) -> str:
    if 'key="F13"' in xml_text or "key='F13'" in xml_text:
        updated = xml_text
        if "launch.sh next" not in updated:
            updated = re.sub(
                r"(<keybind key=\"F13\">.*?<command>)(.*?)(</command>)",
                rf"\1{F13_COMMAND}\3",
                updated,
                count=1,
                flags=re.S,
            )
    else:
        close = "</keyboard>"
        index = xml_text.rfind(close)
        if index < 0:
            raise ValueError("openbox rc.xml has no </keyboard>")
        updated = xml_text[:index] + F13_KEYBIND + "  " + xml_text[index:]
    return _ensure_app_rules(updated)


def _ensure_app_rules(xml_text: str) -> str:
    if 'class="skip-htpc-netflix"' in xml_text and 'class="skip-htpc-areena"' in xml_text:
        return xml_text
    close = "</applications>"
    index = xml_text.rfind(close)
    if index >= 0:
        return xml_text[:index] + APP_RULES + "  " + xml_text[index:]
    end = "</openbox_config>"
    index = xml_text.rfind(end)
    if index < 0:
        raise ValueError("openbox rc.xml has no </openbox_config>")
    block = "  <applications>\n" + APP_RULES + "  </applications>\n"
    return xml_text[:index] + block + xml_text[index:]
