"""
Minimal pure-Python library that demonstrates a basic workflow for an
encrypted order book by leveraging a secure multi-party computation (MPC)
`protocol <https://eprint.iacr.org/2023/1740>`__.
"""
from __future__ import annotations
from typing import Optional, Dict, List, Tuple, Sequence, Iterable
import doctest
from modulo import modulo
import tinynmc

class node:
    """
    Data structure for maintaining the information associated with a node
    and performing node operations.

    Suppose that a workflow is supported by three parties. The :obj:`node`
    objects would be instantiated locally by each of these three parties.

    >>> nodes = [node(), node(), node()]

    The preprocessing workflow that the nodes must execute can be simulated
    using the :obj:`preprocess` function. It is assumed that all permitted
    prices are integers greater than or equal to ``0`` and strictly less
    than a fixed maximum value. The number of distinct prices must be supplied
    to the :obj:`preprocess` function.

    >>> preprocess(nodes, prices=16)

    A request must be submitted for the opportunity to submit an order. The
    clients can create :obj:`request` instances for this purpose. Below, two
    clients each create their request.

    >>> request_ask = request.ask()
    >>> request_bid = request.bid()

    Each client can deliver their request to each node, and each node can then
    locally use its :obj:`masks` method to generate masks that can be returned
    to the requesting client.

    >>> masks_ask = [node.masks(request_ask) for node in nodes]
    >>> masks_bid = [node.masks(request_bid) for node in nodes]

    Each client can then generate locally an :obj:`order` instance (*i.e.*, a
    masked representation of the order).

    >>> order_ask = order(masks_ask, 4)
    >>> order_bid = order(masks_bid, 9)

    Each client can broadcast its masked order to all the nodes. Each node can
    locally assemble these as they arrive. Once a node has received both masked
    orders, it can determine its shares of the overall outcome using the
    :obj:`outcome` method.

    >>> shares = [node.outcome(order_ask, order_bid) for node in nodes]

    The overall outcome can be reconstructed from the shares by the workflow
    operator using the :obj:`reveal` function. The outcome is either ``None``
    (if the bid price does not equal or exceed the ask price) or a :obj:`range`
    instance representing the bid-ask spread (where for a :obj:`range` instance
    ``r``, the ask price is ``min(r)`` and the bid price is ``max(r)``).

    >>> reveal(shares)
    range(4, 10)
    >>> min(reveal(shares))
    4
    >>> max(reveal(shares))
    9

    In the example below, the bid price does not exceed the price of the ask.

    >>> order_ask = order(masks_ask, 11)
    >>> order_bid = order(masks_bid, 7)
    >>> shares = [node.outcome(order_ask, order_bid) for node in nodes]
    >>> reveal(shares) is None
    True
    """
    def __init__(self: node):
        """
        Create a node instance and initialize its private attributes.
        """
        self._signature: List[int] = None
        self._prices: int = None
        self._nodes: List[tinynmc.node] = None

    def masks( # pylint: disable=redefined-outer-name
            self: node,
            request: Iterable[Tuple[int, int]]
        ) -> List[Dict[Tuple[int, int], modulo]]:
        """
        Return masks for a given request.

        :param request: Request from client.
        """
        return [ # pylint: disable=unsubscriptable-object
            tinynmc.node.masks(self._nodes[i], request)
            for i in range(self._prices)
        ]

    def outcome(self: node, ask: Sequence[order], bid: Sequence[order]) -> List[modulo]:
        """
        Perform computation to determine a share of the overall workflow
        outcome that represents the bid-ask spread.

        :param votes: Sequence of masked orders.
        """
        orders: List[Sequence[order]] = [ask, bid]
        prices: int = len(ask)
        return [ # pylint: disable=unsubscriptable-object
            self._nodes[i].compute(self._signature, [order[i] for order in orders])
            for i in range(prices)
        ]

class request(List[Tuple[int, int]]):
    """
    Data structure for representing a request to submit an order. A request
    can be submitted to each node to obtain corresponding masks for an order.

    Instances should only be constructed using the :obj:`request.ask` and
    :obj:`request.bid` methods.
    """
    def __init__(self: request):
        """
        An instance should only be constructed using the :obj:`request.ask`
        or :obj:`request.bid` methods.
        """

    @staticmethod
    def ask() -> request:
        """
        Create a request to submit an ask order.

        >>> request.ask()
        [(0, 0), (1, 0)]
        """
        request_ = request()
        request_.extend([(0, 0), (1, 0)])
        return request_

    @staticmethod
    def bid() -> request:
        """
        Create a request to submit a bid order.

        >>> request.bid()
        [(0, 1), (2, 0)]
        """
        request_ = request()
        request_.extend([(0, 1), (2, 0)])
        return request_

class order(list):
    """
    Data structure for representing an order that can be broadcast to nodes.

    :param masks: Collection of masks to be applied to the order.
    :param price: Non-negative integer representing the order price.

    Suppose masks have already been obtained from the nodes via the steps
    below.

    >>> nodes = [node(), node(), node()]
    >>> preprocess(nodes, prices=16)
    >>> price = 7
    >>> masks = [node.masks(request.ask()) for node in nodes]

    This method can be used to mask the order (in preparation for broadcasting
    it to the nodes).
    
    >>> isinstance(order(masks, price), order)
    True
    """
    def __init__(
            self: order,
            masks: List[List[Dict[Tuple[int, int], modulo]]],
            price: int
        ):
        """
        Create a masked order that can be broadcast to nodes.
        """
        prices: int = len(masks[0])
        for i in range(prices):
            masks_i = [mask[i] for mask in masks]

            coordinate_to_value = {}
            kind = list(masks_i[0].keys())[0][1]
            for key in masks_i[0]:
                sign = 1 if key[0] == 0 else -1
                coordinate_to_value[key] = \
                    sign * ((1 + kind) if i < (price + kind) else (2 - kind))

            self.append(tinynmc.masked_factors(coordinate_to_value, masks_i))

def preprocess(nodes: Sequence[node], prices: int):
    """
    Simulate a preprocessing workflow among the supplied nodes for a workflow
    that supports the specified number of distinct prices (where prices are
    assumed to be integers greater than or equal to ``0`` and strictly less
    than the value ``prices``).

    :param nodes: Collection of nodes involved in the workflow.
    :param prices: Number of distinct prices (from ``0`` to ``prices - 1``).

    The example below performs a preprocessing workflow involving three nodes.

    >>> nodes = [node(), node(), node()]
    >>> preprocess(nodes, prices=16)
    """
    # pylint: disable=protected-access
    signature: List[int] = [2, 1, 1]

    for node_ in nodes:
        node_._signature = signature
        node_._prices = prices
        node_._nodes = [tinynmc.node() for _ in range(prices)]

    for i in range(prices):
        tinynmc.preprocess(signature, [node_._nodes[i] for node_ in nodes])

def reveal(shares: List[List[modulo]]) -> Optional[range]:
    """
    Reconstruct the overall workflow outcome (representing the bid-ask spread)
    from the shares obtained from each node.

    :param shares: Shares of overall outcome (where each share is a list in
        which each entry corresponds to one of the permitted price values).

    Suppose the shares below are returned from the three nodes in a workflow.

    >>> from modulo import modulo
    >>> p = 340282366920938463463374607431768196007
    >>> shares = [
    ...     [
    ...         modulo(191698724691236883130020433754311906556, p),
    ...         modulo(192553930942215974753329735796719934503, p),
    ...         modulo(96579911660242665783999103846211668558, p)
    ...     ],
    ...     [
    ...         modulo(203604595735418244883008588068488824844, p), 
    ...         modulo(213569286850324010515175569194586924260, p), 
    ...         modulo(97156260151248494516609766219626086128, p)
    ...     ], 
    ...     [
    ...         modulo(285261413415221798913720193040735660613, p), 
    ...         modulo(274441516049336941658243909872229533251, p), 
    ...         modulo(146546195109447303162765737365930441321, p)
    ...     ]
    ... ]

    This method combines such shares into an overall workflow outcome by
    reconstructing the individual components and extracting the bid-ask
    spread (if possible). In particular, the output is either ``None`` (if
    the bid price does not equal or exceed the ask price) or a :obj:`range`
    instance representing the bid-ask spread (where for a :obj:`range` instance
    ``r``, the ask price is ``min(r)`` and the bid price is ``max(r)``).

    >>> reveal(shares)
    range(1, 3)
    """
    prices: int = len(shares[0])
    result: List[int] = [
        int(sum(share[i] for share in shares) + 2) - 1
        for i in range(prices)
    ]

    if set(result) == {0}:
        return None

    result.append(0)
    ask: int = result.index(1)
    return range(ask, ask + result[ask + 1:].index(0) + 1)

if __name__ == '__main__':
    doctest.testmod() # pragma: no cover
