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
            m = getattr(self, to_state_name)
        except AttributeError:
            return None

        r = m(state_store, from_state)
        if r != None:
            from_state_name = state_store.name(from_state)
            r = '{} -> {}: {}'.format(from_state_name, to_state_name, r)

        return r


    def INSUFFICIENT_FUNDS(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'
        if from_state & state_store.IN_NETWORK:
            return 'already in network'


    def UNKNOWN_ERROR(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'
        if from_state & state_store.RESERVED:
            return 'not reserved'
        if from_state & state_store.mask_error:
            return 'already in error state'


    def NODE_ERROR(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'
        if from_state & state_store.IN_NETWORK:
            return 'already in network'
        if not from_state & state_store.RESERVED:
            return 'not reserved'
        if from_state & state_store.mask_error:
            return 'already in error state'


    def NETWORK_ERROR(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'
        if from_state & state_store.IN_NETWORK:
            return 'already in network'


    def OBSOLETE(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'
        if from_state & state_store.IN_NETWORK:
            return 'already in network'
        if from_state & state_store.OBSOLETE:
            return 'already obsolete'

    
    def MANUAL(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'


    def QUEUED(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'
        if from_state & state_store.IN_NETWORK:
            if not from_state & state_store.mask_error:
                return 'not in error state'
        elif from_state & state_store.mask_error:
            return 'no first send on error state'
          

    def SENDFAIL(self, state_store, from_state):
        return self.NODE_ERROR(state_store, from_state)


    def FINAL(self, state_store, from_state):
        if from_state & state_store.FINAL:
            return 'already finalized'


    def _MINEFAIL(self, state_store, from_state):
        return self.NETWORK_ERROR(state_store, from_state)


    def _CANCEL(self, state_store, from_state):
        if from_state:
            if from_state & state_store.FINAL:
                return 'already finalized'
            if not from_state & (state_store.OBSOLETE | state_store.IN_NETWORK):
                return 'can only cancel state having OBSOLETE and/or IN_NETWORK'


class Status(shep.persist.PersistedState):
   
    def __init__(self, store_factory, allow_invalid=False, event_callback=None):
        verify = Verify().verify
        self.set_default_state('PENDING')
        super(Status, self).__init__(store_factory, 12, verifier=verify, check_alias=not allow_invalid, event_callback=event_callback)
        self.add('QUEUED')
        self.add('RESERVED')
        self.add('IN_NETWORK')
        self.add('DEFERRED')
        self.add('INSUFFICIENT_FUNDS')
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
        self.alias('REVERTED', self.IN_NETWORK | self.FINAL | self.NETWORK_ERROR)
        self.alias('SUCCESS', self.IN_NETWORK | self.FINAL)
        self.alias('_MINEFAIL', self.FINAL | self.NETWORK_ERROR)
        self.alias('_CANCEL', self.FINAL | self.OBSOLETE)

        self.mask_error = self.LOCAL_ERROR | self.NODE_ERROR | self.NETWORK_ERROR | self.UNKNOWN_ERROR
