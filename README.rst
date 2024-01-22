========
tinybook
========

Minimal pure-Python library that demonstrates a basic workflow for an encrypted order book by leveraging a secure multi-party computation (MPC) `protocol <https://eprint.iacr.org/2023/1740>`__.

|pypi| |readthedocs| |actions| |coveralls|

.. |pypi| image:: https://badge.fury.io/py/tinybook.svg
   :target: https://badge.fury.io/py/tinybook
   :alt: PyPI version and link.

.. |readthedocs| image:: https://readthedocs.org/projects/tinybook/badge/?version=latest
   :target: https://tinybook.readthedocs.io/en/latest/?badge=latest
   :alt: Read the Docs documentation status.

.. |actions| image:: https://github.com/choosek/tinybook/workflows/lint-test-cover-docs/badge.svg
   :target: https://github.com/choosek/tinybook/actions/workflows/lint-test-cover-docs.yml
   :alt: GitHub Actions status.

.. |coveralls| image:: https://coveralls.io/repos/github/choosek/tinybook/badge.svg?branch=main
   :target: https://coveralls.io/github/choosek/tinybook?branch=main
   :alt: Coveralls test coverage summary.

Purpose
-------
This library demonstrates how a functionality can be implemented using a `secure multi-party computation (MPC) protocol <https://eprint.iacr.org/2023/1740>`__ for evaluating arithmetic sum-of-products expressions (as implemented in `tinynmc <https://pypi.org/project/tinynmc>`__). The approach used in this library can serve as a template for any workflow that relies on multiple simultaneous instances of such a protocol.

Installation and Usage
----------------------
This library is available as a `package on PyPI <https://pypi.org/project/tinybook>`__:

.. code-block:: bash

    python -m pip install tinybook

The library can be imported in the usual way:

.. code-block:: python

    import tinybook
    from tinybook import *

Basic Example
^^^^^^^^^^^^^

.. |node| replace:: ``node``
.. _node: https://tinybook.readthedocs.io/en/0.1.0/_source/tinybook.html#tinybook.tinybook.node

Suppose that a secure decentralized voting workflow is supported by three parties. The |node|_ objects would be instantiated locally by each of
these three parties:

.. code-block:: python

    >>> nodes = [node(), node(), node()]

The preprocessing workflow that the nodes must execute can be simulated. It is assumed that all permitted prices are integers greater than or equal to ``0`` and strictly less than a fixed maximum value. The number of distinct prices can be supplied to the preprocessing simulation:

.. code-block:: python

    >>> preprocess(nodes, prices=16)

A request must be submitted for the opportunity to submit an order. Below, two clients each create their request (one for an ask order and the other for a bid order):

.. code-block:: python

    >>> request_ask = request.ask()
    >>> request_bid = request.bid()

Each client can deliver their request to each node, and each node can then locally generate masks that can be returned to the requesting client:

.. code-block:: python

    >>> masks_ask = [node.masks(request_ask) for node in nodes]
    >>> masks_bid = [node.masks(request_bid) for node in nodes]

.. |order| replace:: ``order``
.. _order: https://tinybook.readthedocs.io/en/0.1.0/_source/tinybook.html#tinybook.tinybook.order

Each client can then generate locally an |order|_ instance (*i.e.*, a masked representation of the order):

.. code-block:: python

    >>> order_ask = order(masks_ask, 4)
    >>> order_bid = order(masks_bid, 9)

Each client can broadcast its masked order to all the nodes. Each node can locally assemble these as they arrive. Once a node has received both masked orders, it can determine its shares of the overall outcome:

.. code-block:: python

    >>> shares = [node.outcome(order_ask, order_bid) for node in nodes]

.. |range| replace:: ``range``
.. _range: https://docs.python.org/3/library/functions.html#func-range

The overall outcome can be reconstructed from the shares by the workflow operator. The outcome is either ``None`` (if the bid price does not equal or exceed the ask price) or a |range|_ instance representing the bid-ask spread (where for a |range|_ instance ``r``, the ask price is ``min(r)`` and the bid price is ``max(r)``):

.. code-block:: python

    >>> reveal(shares)
    range(4, 10)
    >>> min(reveal(shares))
    4
    >>> max(reveal(shares))
    9

Development
-----------
All installation and development dependencies are fully specified in ``pyproject.toml``. The ``project.optional-dependencies`` object is used to `specify optional requirements <https://peps.python.org/pep-0621>`__ for various development tasks. This makes it possible to specify additional options (such as ``docs``, ``lint``, and so on) when performing installation using `pip <https://pypi.org/project/pip>`__:

.. code-block:: bash

    python -m pip install .[docs,lint]

Documentation
^^^^^^^^^^^^^
The documentation can be generated automatically from the source files using `Sphinx <https://www.sphinx-doc.org>`__:

.. code-block:: bash

    python -m pip install .[docs]
    cd docs
    sphinx-apidoc -f -E --templatedir=_templates -o _source .. && make html

Testing and Conventions
^^^^^^^^^^^^^^^^^^^^^^^
All unit tests are executed and their coverage is measured when using `pytest <https://docs.pytest.org>`__ (see the ``pyproject.toml`` file for configuration details):

.. code-block:: bash

    python -m pip install .[test]
    python -m pytest

Alternatively, all unit tests are included in the module itself and can be executed using `doctest <https://docs.python.org/3/library/doctest.html>`__:

.. code-block:: bash

    python src/tinybook/tinybook.py -v

Style conventions are enforced using `Pylint <https://pylint.readthedocs.io>`__:

.. code-block:: bash

    python -m pip install .[lint]
    python -m pylint src/tinybook

Contributions
^^^^^^^^^^^^^
In order to contribute to the source code, open an issue or submit a pull request on the `GitHub page <https://github.com/choosek/tinybook>`__ for this library.

Versioning
^^^^^^^^^^
The version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`__.

Publishing
^^^^^^^^^^
This library can be published as a `package on PyPI <https://pypi.org/project/tinybook>`__ by a package maintainer. First, install the dependencies required for packaging and publishing:

.. code-block:: bash

    python -m pip install .[publish]

Ensure that the correct version number appears in ``pyproject.toml``, and that any links in this README document to the Read the Docs documentation of this package (or its dependencies) have appropriate version numbers. Also ensure that the Read the Docs project for this library has an `automation rule <https://docs.readthedocs.io/en/stable/automation-rules.html>`__ that activates and sets as the default all tagged versions. Create and push a tag for this version (replacing ``?.?.?`` with the version number):

.. code-block:: bash

    git tag ?.?.?
    git push origin ?.?.?

Remove any old build/distribution files. Then, package the source into a distribution archive:

.. code-block:: bash

    rm -rf build dist src/*.egg-info
    python -m build --sdist --wheel .

Finally, upload the package distribution archive to `PyPI <https://pypi.org>`__:

.. code-block:: bash

    python -m twine upload dist/*
