def check_uid_is_valid(uid: str) -> bool:
    if uid.isdigit():
        return (len(uid) == 9) and uid[0] in ['1', '2', '5']
    else:
        return False


def check_cookie_is_valid(cookie: str) -> bool:
    return '_MHYUUID' in cookie and len(cookie) > 20
