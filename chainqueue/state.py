# standard imports
import logging

# external imports
import shep.persist

logg = logging.getLogger(__name__)


class Verify:

    def verify(self, state_store, from_state, to_state):
        to_state_name = state_store.name(to_state)
        m = None
        try:  
            m = getattr(self, 'verify_' + to_state_name)
        except AttributeError:
            logg.debug('foo {}'.format(to_state_name))
            return None

        r = m(state_store, from_state)
        if r != None:
            from_state_name = state_store.name(from_state)
            r = '{} -> {}: {}'.format(from_state_name, to_state_name, r)

        return r


    def verify_GAS_ISSUES(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'
        if from_state & state_store.GAS_ISSUES:
            return 'already in network'



class Status(shep.persist.PersistedState):
   
    def __init__(self, store_factory):
        verify = Verify().verify
        self.set_default_state('PENDING')
        super(Status, self).__init__(store_factory, 12, verifier=verify)
        self.add('QUEUED')
        self.add('RESERVED')
        self.add('IN_NETWORK')
        self.add('DEFERRED')
        self.add('GAS_ISSUES')
        self.add('LOCAL_ERROR')
        self.add('NODE_ERROR')
        self.add('NETWORK_ERROR')
        self.add('UNKNOWN_ERROR')
        self.add('FINAL')
        self.add('OBSOLETE')
        self.add('MANUAL')

        self.alias('SENDFAIL', self.DEFERRED | self.LOCAL_ERROR)
        self.alias('RETRY', self.DEFERRED | self.QUEUED)
        self.alias('OBSOLETED', self.OBSOLETE | self.IN_NETWORK)
        self.alias('FUBAR', self.FINAL | self.UNKNOWN_ERROR)
        self.alias('CANCELLED', self.IN_NETWORK | self.FINAL | self.OBSOLETE)
        self.alias('OVERRIDDEN', self.FINAL | self.OBSOLETE | self.MANUAL)
        self.alias('REJECTED', self.NODE_ERROR | self.FINAL)
        self.alias('REVERTED', self.IN_NETWORK | self.FINAL, self.NETWORK_ERROR)
        self.alias('SUCCESS', self.IN_NETWORK | self.FINAL)

