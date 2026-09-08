import random

def generate_token():
    # Generates a random 20-digit token
    return ''.join([str(random.randint(0, 9)) for _ in range(20)])