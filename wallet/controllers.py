from .models import Wallet, Contract
from .web3 import getAccount, getBalance, sendEther, unlockAccount, deployContract, getContract, checksumAddress
import json


class WalletHandler():
    """
    노드와 미들웨어간 지갑 관리를 지원하는 핸들러입니다.
    """

    @staticmethod
    def findAddress(user_id):
        """
        사용자의 지갑주소를 반환합니다.
        """
        return Wallet.objects.filter(user_id=user_id).first()

    def makeWallet(self, user_id, password):
        """
        사용자 지갑을 생성합니다.
        노드와 미들웨어간 정보를 동기화합니다.
        """
        account = getAccount(user_id)           # Web3 통해서 먼저 어드레스를 받아오고
        wallet = Wallet(user_id=user_id, password=password, address=account['address'],
                        private_key=user_id)    # 사용자 정보를 추합하여
        wallet.save()                           # DB에 저장
        return wallet

    def findWallet(self, user_id, password):
        """
        지갑정보를 검색 후 반환합니다.
        """
        if not user_id or not password:
            raise AssertionError

        account = Wallet.objects.filter(
            user_id=user_id, password=password).first()
        return account

    def keystore(self):
        """
        전체 사용자 지갑 정보를 반환합니다.
        """
        return Wallet.objects.all()

    def getRest(self, user_id):
        """
        사용자의 지갑 잔액을 반환합니다.
        """
        if not user_id:
            raise AssertionError

        account = self.findAddress(user_id=user_id)
        return getBalance(address=account.address)

    def transferEther(self, sender, receiver, amount):
        """
        이더리움을 송금합니다.
        """
        if not sender or not receiver or not amount:
            raise ValueError

        sender_address = self.findAddress(sender)
        receiver_address = self.findAddress(receiver)

        print('Sender :', sender)
        print('Sender_address: ', sender_address)
        print('Receiver: ', receiver)
        print('Receiver_address: ', receiver_address)

        # 트랜잭션 수행 전 계정 언락
        val_1 = unlockAccount(sender, str(sender_address), 1000)
        val_2 = unlockAccount(receiver, str(receiver_address), 1000)

        if val_1 is False or val_2 is False:
            raise ValueError

        transaction_result = sendEther(
            sender=str(sender_address), receiver=str(receiver_address), amount=amount)

        return transaction_result


class ContractHandler():
    """
    ERC20 Token 메인 인터페이스를 호출하는 핸들러입니다.
    """

    def initContract(self, user_id, address):
        """
        Deploy Contract
        """
        val_1 = unlockAccount(user_id=user_id, address=address, duration=1000)

        if val_1 is False:
            raise ValueError

        tx_receipt = deployContract(address=address)
        print('Block Number: ', tx_receipt['blockNumber'])
        print('Gas Used: ', tx_receipt['gasUsed'])
        print('CA: ', tx_receipt['contractAddress'])
        print('From: ', tx_receipt['from'])

        contract = Contract(
            address=tx_receipt['contractAddress'], owner=tx_receipt['from'], block_number=tx_receipt['blockNumber'])
        contract.save()

        return contract

    def getAllFunctions(self, ca):
        """
        스마트 컨트랙트의 모든 함수를 조회합니다.
        """
        contract = getContract(address=ca)
        result = contract.all_functions()
        print('Functions: ', str(result))
        return str(result)

    def totalSupply(self, ca):
        """
        Total Supply
        """

        contract = getContract(address=ca)
        result = contract.functions.totalSupply().call()

        return result

    def balanceOf(self, user_id, address, ca):
        """
        Check balance of User
        """

        val_1 = unlockAccount(user_id=user_id, address=address, duration=1000)

        if val_1 is False:
            raise ValueError

        contract = getContract(address=ca)
        checksum_address = checksumAddress(address)
        result = contract.functions.balanceOf(checksum_address).call()

        return result

    def transferToken(self, receiver, amount, ca):
        """
        Transfer Token To
        """

        val_1 = unlockAccount(
            user_id=receiver['userId'], address=receiver['address'], duration=1000)

        if val_1 is False:
            return ValueError

        contract = getContract(address=ca)
        checksum_address = checksumAddress(receiver['address'])
        result = contract.functions.transfer(
            checksum_address, amount).transact()

        print('Transaction Result: ', result)
        return result

    def transferTokenFrom(self, sender, receiver, amount, ca):
        """
        Transfer Token From - To
        """

        val_1 = unlockAccount(
            user_id=sender['userId'], address=sender['address'], duration=1000)
        val_2 = unlockAccount(
            user_id=receiver['userId'], address=receiver['address'], duration=1000)

        if val_1 is False or val_2 is False:
            raise ValueError

        contract = getContract(address=ca)

        print(contract.functions.transferFrom(
            sender['address'], receiver['address'], amount).call())

        return True

    def callFunction(self, func_name, ca):
        """
        Call funtions of Contract
        """

        # 딕셔너리 맵핑
        # RPC from client as front end method
        rpc_list = {'getBalance': 'balanceOf',
                    'getSupploy': 'totalSupply'}

        contract = getContract(address=ca)
        selected_function = rpc_list[func_name]

        print(contract.functions[selected_function]().call())

        return True


class Test():
    """
    테스트를 위한 RPC 를 모아놓은 핸들러입니다.
    """

    def unlockAll(self):
        for wallet in Wallet.objects.all():
            unlockAccount(user_id=wallet.user_id,
                          address=wallet.address, duration=1000)

        return True
