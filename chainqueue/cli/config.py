def process_config(config, args, flags):
        args_override = {}

        args_override['QUEUE_BACKEND'] = getattr(args, 'backend')
        args_override['TX_DIGEST_SIZE'] = getattr(args, 'tx_digest_size')
        args_override['QUEUE_STATE_PATH'] = getattr(args, 'state_dir')

        config.dict_override(args_override, 'local cli args')

        return config
