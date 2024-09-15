import re
import base64

def is_base32_encoded(s):
    """
    Check if a string is Base32 encoded.

    :param s: The string to check.
    :return: True if the string is Base32 encoded, False otherwise.
    """
    if not re.fullmatch(r'[A-Z2-7=]+', s):
        return False

    if len(s) % 8 != 0:
        return False

    try:
        # Attempt to decode the Base32 string
        base64.b32decode(s, casefold=True)
        return True
    except:
        return False