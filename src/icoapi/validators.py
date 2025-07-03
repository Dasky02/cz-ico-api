def is_valid_ico(ico: str) -> bool:
    if not (ico.isdigit() and len(ico) == 8):
        return False
    nums = list(map(int, ico))
    control = sum(n * w for n, w in zip(nums[:7], range(8, 1, -1))) % 11
    check = {0: 1, 1: 0}.get(control, 11 - control)
    return check == nums[-1]

def is_valid_dic(dic: str) -> bool:
    return dic.startswith("CZ") and is_valid_ico(dic[2:])
