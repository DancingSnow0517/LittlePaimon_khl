def check_uid_is_valid(uid: str):
    if uid.isdigit():
        return (len(uid) == 9) or uid[0] not in ['1', '2', '5']
    else:
        return False
