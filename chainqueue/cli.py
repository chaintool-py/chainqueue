# standard imports
import logging
import enum

# external imports
from hexathon import add_0x

# local imports
from chainqueue.enum import (
        StatusBits,
        all_errors,
        is_alive,
        is_error_status,
        status_str,
        )

logg = logging.getLogger(__name__)


class OutputCol(enum.Enum):
    chainspec = 0
    hash = 1
    statustext = 2
    statuscode = 3
    signedtx = 4


class Outputter:
    """Output helper for chainqueue cli listings tools.

    :param chain_spec: Chain spec to use as getter context
    :type chain_spec: chainlib.chain.ChainSpec
    :param writer: Writer to write output to. Will automatically flush.
    :type writer: Writer
    :param getter: Transaction getter
    :type getter: See chainqueue.sql.backend.get_otx 
    :param session_method: Backend session generator method
    :type session_method: varies
    :param decode_status: Print status bit details
    :type decode_status: bool
    """

    all_cols = [
            OutputCol.chainspec,
            OutputCol.hash,
            OutputCol.signedtx,
            OutputCol.statustext,
            OutputCol.statuscode,
            ]
    default_cols = [
            OutputCol.chainspec,
            OutputCol.hash,
            OutputCol.statustext,
            OutputCol.statuscode,
            ]

    def __init__(self, chain_spec, writer, getter, session_method=None, decode_status=True, cols=None):
        self.decode_status = decode_status
        self.writer = writer
        self.getter = getter
        self.chain_spec = chain_spec
        self.chain_spec_str = str(chain_spec)
        self.session = None
        if session_method != None:
            self.session = session_method()
        self.results = {
            'pending_error': 0,
            'final_error': 0,
            'pending': 0,
            'final': 0,
                }

        debug_col_name = []
        if cols == None:
            self.cols = Outputter.default_cols
        else:
            self.cols = []
            for col in cols:
                v = getattr(OutputCol, col)
                self.cols.append(v) 

        for col in self.cols:
            debug_col_name.append(col.name)
        logg.debug('outputter initialized with cols: {}'.format(','.join(debug_col_name)))


    def __del__(self):
        if self.session != None:
            self.session.close()


    def add(self, tx_hash):
        """Retrieve a transaction by hash and add it for summary output generation.

        :param tx_hash: Transaction hash
        :type tx_hash: str
        """
        tx = self.getter(self.chain_spec, tx_hash, session=self.session)
        self.__add(tx)

    def __add(self, tx):
        category = None
        if is_alive(tx['status_code']):
            category = 'pending'
        else:
            category = 'final'
        self.results[category] += 1
        if is_error_status(tx['status_code']):
            logg.debug('registered {} as {} with error'.format(tx['tx_hash'], category))
            self.results[category + '_error'] += 1
        else:
            logg.debug('registered {} as {}'.format(tx['tx_hash'], category))
     

    def decode_summary(self):
        """Writes summary to the registered writer.
        """
        self.writer.write('pending\t{}\t{}\n'.format(self.results['pending'], self.results['pending_error']))
        self.writer.write('final\t{}\t{}\n'.format(self.results['final'], self.results['final_error']))
        self.writer.write('total\t{}\t{}\n'.format(self.results['final'] + self.results['pending'], self.results['final_error'] + self.results['pending_error']))


    def decode_single(self, tx_hash):
        """Retrieves the transaction with the given hash and writes the details to the underlying writer.

        Registers the transaction with the summary generator.

        :param tx_hash: Transaction hash
        :type tx_hash: str
        """
        tx = self.getter(self.chain_spec, tx_hash, session=self.session)
        self.__add(tx)
        status = tx['status']
        if self.decode_status:
            status = status_str(tx['status_code'], bits_only=True)

        vals = [
            self.chain_spec_str,
            add_0x(tx_hash),
            status,
            str(tx['status_code']),
            add_0x(tx['signed_tx']),
            ]

        i = 0
        l = len(self.cols)
        for col in self.cols:
            self.writer.write(vals[col.value])
            i += 1
            if i == l:
                self.writer.write('\n')
            else:
                self.writer.write('\t')
