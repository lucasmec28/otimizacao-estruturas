"""Bounded wall time and optional cooperative cancellation; never partial success."""
import math
import time

class ExecutionLimit(RuntimeError):
    pass

class ExecutionBudget:
    def __init__(self,max_seconds=180.,cancelled=None):
        if isinstance(max_seconds,bool) or not isinstance(max_seconds,(int,float)) or not math.isfinite(max_seconds) or max_seconds<=0:
            raise ValueError('Prazo de execução deve ser positivo e finito.')
        self.start=time.monotonic();self.max_seconds=float(max_seconds);self.cancelled=cancelled
    @property
    def elapsed(self):return time.monotonic()-self.start
    def check(self):
        if self.cancelled and self.cancelled():raise ExecutionLimit('Execução cancelada; nenhum resultado incompleto foi liberado.')
        if self.elapsed>self.max_seconds:raise ExecutionLimit(f'Prazo de {self.max_seconds:g} s excedido; nenhum resultado incompleto foi liberado. Reduza a seleção ou tente após a restrição de CPU da hospedagem terminar.')
