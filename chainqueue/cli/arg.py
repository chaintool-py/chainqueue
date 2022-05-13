def process_flags(argparser, flags):
    argparser.add_argument('--backend', type=str, help='Backend to use for state store')
    argparser.add_argument('--tx-digest-size', dest='tx_digest_size', type=str, help='Size of transaction hash in bytes')
    argparser.add_argument('--state-dir', dest='state_dir', type=str, help='Directory to store queuer state in')
