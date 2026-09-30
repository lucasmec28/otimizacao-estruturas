"""Display identifiers: filas in +Y, numbered axes in +X."""
def fila(index):
    if not isinstance(index,int) or index<1:raise ValueError('Fila deve ser positiva.')
    result=''
    while index:
        index,remainder=divmod(index-1,26)
        result=chr(65+remainder)+result
    return result


def base(row,column):
    return f'{fila(int(row))}{int(column)}'


def member(identifier):
    kind,row,col=identifier.split('-');row=int(row);col=int(col)
    if kind=='C':return f'C-{base(row,col)}'
    if kind=='VP':return f'VP-{fila(row)}-{col}/{col+1}'
    return f'VS-{fila(row)}/{fila(row+1)}-S{col}'
