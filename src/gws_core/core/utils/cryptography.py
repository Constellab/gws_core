

from cryptography.fernet import Fernet


class Cryptography:
    """ Symmetric encryption utility """
    # -- D --

    @staticmethod
    def decrypt_message(key, encrypted_message):
        """
        Decrypts an encrypted message
        """

        fernet = Fernet(key)
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()

    # -- E --

    @staticmethod
    def encrypt_message(key, message):
        """
        Encrypts a message
        """

        fernet = Fernet(key)
        encrypted_message = fernet.encrypt(message.encode())
        return encrypted_message.decode()

    # -- G --

    @staticmethod
    def generate_key():
        """
        Generates a key and save it into a file
        """

        return Fernet.generate_key()
