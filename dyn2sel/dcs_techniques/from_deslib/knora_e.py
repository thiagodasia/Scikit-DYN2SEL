from dyn2sel.dcs_techniques.from_deslib.deslib_interface import DESLIBInterface
import deslib.des as deslib


class KNORAE(DESLIBInterface):
    def _get_stencil(self):
        return deslib.KNORAE
