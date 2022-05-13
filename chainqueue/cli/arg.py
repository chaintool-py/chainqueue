def apply_flag(flag):
    flag.add('queue')
    return flag


def apply_arg(arg): 
    arg.add_long('tx-digest-size', 'queue', type=int, help='Size of transaction hash in bytes')
    return arg
