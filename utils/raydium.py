import requests

RAYDIUM_API_URL = "https://api-v3.raydium.io"
WSOL_ADDRESS = 'So11111111111111111111111111111111111111112'


def get_pool_quote_token_info(pool_id: str):
    url = f'{RAYDIUM_API_URL}/pools/info/ids?ids={pool_id}'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if data['success'] and data['data'] and data['data'][0] is not None:
        mint_address = data['data'][0]['mintB']['address']
        if mint_address != WSOL_ADDRESS:
            return data['data'][0]['mintB']
        else:
            return data['data'][0]['mintA']
    else:
        raise Exception(f"Invalid pool_id or no data found for pool_id: {pool_id}")


def get_pool_info(pool_id: str):
    url = f'{RAYDIUM_API_URL}/pools/info/ids?ids={pool_id}'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if data['success'] and data['data'] and data['data'][0] is not None:
        mint_address = data['data'][0]['mintB']['address']
        if mint_address != WSOL_ADDRESS:
            return data['data'][0], True
        else:
            return data['data'][0], False
    else:
        raise Exception(f"Invalid pool_id or no data found for pool_id: {pool_id}")


def get_pool_address_from_mint(mint_address: str):
    if mint_address == WSOL_ADDRESS:
        return Exception(f"You can't use mint address as mint")
    url = f'{RAYDIUM_API_URL}/pools/info/mint?mint1={WSOL_ADDRESS}&mint2={mint_address}&poolType=standard&poolSortField=default&sortType=desc&pageSize=10&page=1'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if data['success'] and data['data']['data'] and data['data']['data'][0] is not None:
        return data['data']['data'][0]['id']
    else:
        raise Exception(f"Can't get data of pools for this mint: {mint_address}")

if __name__ == '__main__':
    print(get_pool_info('GcHDV1oLCKu6nHXfqcv3tpwg9L8qUPxTZSo3u6R6UPYv'))
