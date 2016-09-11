/*
  Slidemenu
*/
(function() {
	var $body = document.body
	, $menu_trigger = $body.getElementsByClassName('menu-trigger')[0];

	if ( typeof $menu_trigger !== 'undefined' ) {
		$menu_trigger.addEventListener('click', function() {
			$body.className = ( $body.className == 'menu-active' )? '' : 'menu-active';
		});
	}

}).call(this);

$(".new").click(function(){
    $("body").removeClass('menu-active')
		console.log("new");
		$('#newModal').modal('show');
		//$('.modal-backdrop').remove();
});

$(".delete").click(function(){
    $("body").removeClass('menu-active')
		console.log("delete");
		$('#deleteModal').modal('show');
});

$(".sync").click(function(){
    $("body").removeClass('menu-active')
		console.log("sync");

});

$(".settings").click(function(){
    $("body").removeClass('menu-active')
		console.log("settings");
		$(".main-panel").css("display","none")
		$(".setting-panel").css("display","block")
});

$("#close-setting").click(function(){
	$(".main-panel").css("display","block")
	$(".setting-panel").css("display","none")
});

$("#floating-button").click(function(){
    $("body").removeClass('menu-active')
		console.log("new");
		$('#newModal').modal('show');
		//$('.modal-backdrop').remove();
});
