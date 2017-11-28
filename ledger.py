from collections import OrderedDict
import matplotlib.pyplot as plt
import numpy as np

class Ledger():
    def __init__(self, users):
        super().__init__()
        self.users = users
        self.txs = []

    def __repr__(self):
        return "[{}]".format(",\n ".join([str(tx[0]) for tx in self.txs]))

    def list_with_spentness(self):
        return "[{}]".format(",\n ".join([str(tx[0]) + ", " + str(tx[1]) for tx in self.txs]))

    def add_transaction(self, tx):
        if tx.parent is None:
            self.txs.append([tx, "unspent"])
        else:
            for in_tx in self.txs:
                if in_tx[0].id == tx.parent:
                    if in_tx[1] == "unspent":
                        in_tx[1] = "spent"
                        self.txs.append([tx, "unspent"])
                    elif in_tx[1] in ["spent", "invalid double spend"]:
                        self.txs.append([tx, "invalid double spend"])
                    return

    def get_transactions(self):
        return [tx[0] for tx in self.txs]

    def get_parent_tx(self, tx):
        for in_tx in [tx[0] for tx in self.txs]:
            if in_tx.id == tx.parent:
                return in_tx

    def swap_order(self, a, b):
        txs = [tx[0] for tx in self.txs]
        txs[a], txs[b] = txs[b], txs[a]
        self.txs = []
        for tx in txs:
            self.add_transaction(tx)

    def get_balances(self, allow_doublespends=True):
        balances = OrderedDict()
        for user in self.users:
            balances[user] = 0

        if allow_doublespends:
            # calculate balances on the fly
            for tx in [tx[0] for tx in self.txs]:
                if tx.recipient_name in balances:
                    # Add 1 to the recipient's balance
                    balances[tx.recipient_name] += 1
                if tx.parent is not None:
                    # Remove 1 from the sender's balance
                    balances[self.get_parent_tx(tx).recipient_name] -= 1
        else:
            # calculate balances based on spentness
            for tx in self.txs:
                if tx[1] == "unspent" and tx[0].recipient_name in balances:
                    balances[tx[0].recipient_name] += 1

        return balances

    def draw_balances(self, allow_doublespends=True):
        fig, ax = plt.subplots()
        ind = np.arange(1, 4)

        balances = list(self.get_balances(allow_doublespends).values())

        n0, n1, n2 = plt.bar(ind, balances)

        n0.set_facecolor('r')
        n1.set_facecolor('r')
        n2.set_facecolor('r')
        ax.set_xticks(ind)
        ax.set_xticklabels(self.users)
        ax.set_ylim([0, max(balances) + 1])
        ax.set_yticks([0, 1, 2])
        ax.set_ylabel('Balance')
        ax.set_title('Balances')

        # ask the canvas to re-draw itself the next time it
        # has a chance.
        # For most of the GUI backends this adds an event to the queue
        # of the GUI frameworks event loop.
        fig.canvas.draw()
