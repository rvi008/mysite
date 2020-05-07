MSLQD_URL='https://www.morganstanley.com/im/en-nl/liquidity-investor/product-and-performance/morgan-stanley-liquidity-funds/us-dollar-liquidity-fund.shareClass.QU.html'
BGF = {"LU0122376428":"https://www.blackrock.com/sg/en/terms-and-conditions?targetUrl=%2Fsg%2Fen%2Fproducts%2F229927%2Fbgf-world-energy-fund-a2-sgd-hedged&action=ACCEPT",
"LU0368265764":"https://www.blackrock.com/sg/en/terms-and-conditions?targetUrl=%2Fsg%2Fen%2Fproducts%2F229951%2Fbgf-world-gold-fund-a2-sgd-hedged&action=ACCEPT"}
CURRENCIES_TICKERS = {"usd":"EUR=X", "sgd":"SGDEUR=X", "gbp":"GBPEUR=X"}
GOLD_URL = "https://www.bullionstar.com/sell/"
GOLD_COINS = {
    "OR10USD":"Gold Bullion Coins - 1/2 oz",
    "OR20FR":"French/Austrian/Swiss/Hungarian/Italian/Belgian 20 Francs",
    "OR10FR":"French/Swiss/Hungarian/Italian 10 Francs"
}
SILVER_URL = {"AG1F":"https://www.achat-or-et-argent.fr/argent/5/pieces-francaises",
              "AG50F":"https://www.achat-or-et-argent.fr/argent/5/pieces-francaises",
              "AGPHIL":"https://www.achat-or-et-argent.fr/argent/9/pieces-modernes"}

SILVER_COINS = {
	"AG1F":"1 Franc Semeuse 1898 - 1920",
	"AG50F":"50 Francs Hercule 1974 - 1980",
	"AGPHIL":"Philharmonique 1 Once"
}

CL_URLS = {
	"OCTOBER":"https://app.october.eu/login",
	"ENTREPRETEURS":"https://www.lesentrepreteurs.com/login"
}

CL_NAVIGATION = {
	"OCTOBER":{"login":{"descriptor":"id","desc_values":["ember566", "ember576", "ember613"]},
	"home":{"descriptor":"id", "desc_values":["ember1337"]},
	"extract":{"descriptor":"class", "desc_values":["//h4"], "item_num":-1}},

	"ENTREPRETEURS":{"login":{"descriptor":"id","desc_values":["username", "password", "_submit"]},
	"home":{"descriptor":"class", "desc_values":["valign-wrapper"]},
	"extract":{"descriptor":"class", "desc_values":["//span"], "item_num":9}}
	}

CRYPTO_URL = "https://accounts.binance.com/en/login"
CRYPTO_NAVIGATION = [
{"descriptor":"class","value":"css-txr6gn","action":"click","item_num":0},
{"descriptor":"class","value":"css-sf3qia","action":"input_username","item_num":0},
{"descriptor":"class","value":"css-sf3qia","action":"input_password","item_num":1},
{"descriptor":"class","value":"css-1hv630j","action":"click","item_num":0},
{"descriptor":"xpath","value":"//body","action":"click","item_num":0},
{"descriptor":"class","value":"css-1drhd22","action":"click","item_num":1},
{"descriptor":"xpath","value":"//body","action":"click","item_num":0},
{"descriptor":"class","value":"css-1drhd22","action":"click","item_num":0},
{"descriptor":"xpath","value":"//body","action":"click","item_num":0},
{"descriptor":"class","value":"css-oo58bf","action":"click","item_num":0},
{"descriptor":"xpath","value":"//body","action":"collect","item_num":0}]