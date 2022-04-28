def process_config(config, args, flags):
        args_override = {}

        args_override['QUEUE_BACKEND'] = getattr(args, 'backend')

        config.dict_override(args_override, 'local cli args')

        return config
