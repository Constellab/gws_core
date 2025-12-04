from peewee import Expression


class ExpressionBuilder:
    """Class to buid peewee expression to make select

    :return: [description]
    :rtype: [type]
    """

    _expression: Expression

    def __init__(self, expression: Expression = None) -> None:
        self._expression = expression

    def add_expression(self, expression: Expression) -> None:
        if self._expression is not None:
            self._expression = self._expression & (expression)
        else:
            self._expression = expression

    def build(self) -> Expression:
        return self._expression
