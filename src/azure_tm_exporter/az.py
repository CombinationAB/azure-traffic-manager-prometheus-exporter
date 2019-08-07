import logging
logger = logging.getLogger(__name__)

def az_raw(*args):
    args=[str(arg) for arg in args]
    from azure.cli.core import get_default_cli
    from knack.util import CLIError
    import knack.prompting
    def do_raise():
        logger.error("TTY access requested from Azure CLI - denied")
        ex = knack.prompting.NoTTYException()
        ex.args = ("TTY access requested from Azure CLI",)
        raise ex
    knack.prompting.verify_is_a_tty = do_raise
    
    def do_raise_noparam(missing_parameters, *args, **kwargs):
        logger.warning("Missing parameters:")
        for p in missing_parameters:
            logger.warning("  %s" % p)
        raise CLIError('The following parameters are not defined in the environment: %s' % ', '.join(missing_parameters))
    import azure.cli.command_modules.resource.custom
    azure.cli.command_modules.resource.custom._prompt_for_parameters = do_raise_noparam

    try:
        logger.debug("RUN: az %s" % ' '.join(args))
    except:
        logger.warn("Bad CLI: %s" % repr(args))
        raise

    # Replace default exception handler that raises SystemExit and masks actual exception
    from azure.cli.core.commands import arm
    errs = []
    def _replace_handler(e):
        raise e
    arm.show_exception_handler = _replace_handler
    
    cli = get_default_cli()

    class NullOutput:
        def get_formatter(self, *a):
            return self

        def out(self, result, *args, **kwargs):
            pass

    cli.output = NullOutput()
    def exception_handler(ex):
        errs.append(ex)
        return 1
    cli.exception_handler = exception_handler

    try:
        cli.invoke(list(args))
    except SystemExit as e:
        import traceback
        traceback.print_exc()
        if cli.result is None:
            from knack.util import CommandResultItem
            cli.result = CommandResultItem(None)
        cli.result.exit_code = e.code
    if errs and not cli.result.error:
        cli.result.error = errs[0]
    return cli.result

def az(*args): #NOSONAR
    result = az_raw(*args)
    if result.exit_code != 0:
        raise Exception("Azure CLI error: %s" % result.error)
    return result.result

def az_stdout(*args):
    from contextlib import redirect_stdout
    import io

    std_out_buff = io.StringIO()

    with redirect_stdout(std_out_buff):
        result = az_raw(*args)
        if result.exit_code != 0:
            raise Exception("Azure CLI error: %s" % result.error)

    return std_out_buff.getvalue()
