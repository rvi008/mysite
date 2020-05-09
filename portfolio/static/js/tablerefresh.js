//setInterval(function() {$.ajax({method: "GET",url: "portfolio/stocks",success: function(data) {$("tbody").empty();$.each(data,(key, value)){var asset_id = stock.symbol;var asset_name = stock.symbol;var asset_price = stock.price;var asset_qty = stock.stocks_owned;var asset_buying_price = stock.buying_price;$("tbody").append("<tr><td>" + asset_id + "</td><td>" + asset_name + "</td><td>" + asset_price + "</td><td>" + asset_qty + "</td>" asset_buying_price + "</td></tr>")})}})},3000);
//{
//	$.ajax({method: "GET", url:"/portfolio",success:function(key,data){$("html").empty()}})
//}

setInterval(function(){location.reload();}, 60000);