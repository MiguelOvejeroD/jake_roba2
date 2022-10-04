import hashlib
import hmac
import os

class Security:

    @staticmethod
    def verify_signature(payload_body, x_hub_signature, secret_token):
        #home_dir = os.path.expanduser('~')
        #secret_token = open(os.path.join(home_dir, '.git_secret_token'), 'r').readline().rstrip('\n')
        signature = hmac.new(bytearray(secret_token, 'utf-8'), payload_body, hashlib.sha1).hexdigest()
        split = x_hub_signature.split('=')
        return len(split) > 1 and hmac.compare_digest(signature, split[1])
