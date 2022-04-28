def process_flags(argparser, flags):
    argparser.add_argument('--backend', type=str, help='Backend to use for state store')
