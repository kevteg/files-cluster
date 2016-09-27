var directorios = [];
var grupos = [];
var users = [];
var processes = [];
var interface;
var side_color = "#556270" ;
var side_text_color = "#dfe5eb";
var main_color = "#FF6B6B";

function add_direc()
{
	var dir = $('#add_direc').val();
	var error = false;
	var group = $('#add_grupo').val();
	var user = $('#add_user').val();
	//AQUI SI LA VARIABLE DE INTERFAZ QUE SE CAMBIA EN CONFIGURACIÓN ES DIFERENTE A DEFAULT SE LLAMA CON EL [-i INTERFAZ] SI NO SE LLAMA SIN EL -i:
	const spawn = require('child_process').spawn;
	if (typeof(interface) != 'undefined' && interface != null && interface != "")
	{
	  var ls = spawn('../../backend/write.py', ['-g', group, '-n', user, '-d', dir, '-i', interface]);
	}
	else{
		var ls = spawn('../../backend/write.py', ['-g', group, '-n', user, '-d', dir]);
	}
	console.log(ls);
	ls.stdout.on('data', (data) => {
	  console.log(`stdout: ${data}`);
	});
	var stderr = ''
	ls.stderr.on('data', function(data) {
		console.log(`stderr: ${data}`);
	  stderr += data;
	});

	sleep(1000).then(() => {
		if(!stderr != ''){
			directorios.push(dir);
			grupos.push(group);
			users.push(user);
			$( "#directorys" ).append( "<p> <i class = \"fa fa-refresh fa-spin\"></i>   "+ dir + "<br>   <i class = \"fa fa-users\"></i>   " + group + "<br>   <i class = \"fa fa-user\"></i>   "  + user + "</p>");
			$( "#directorys" ).append( "<div class='directory' id='"+dir+"'>");
			var ruta = '"'+dir +'"';
			$( "#directorys" ).append( "<button onclick='shell("+ruta+")' id='directory-button' class='btn'><i class='fa fa-folder-open-o'></i>Abrir directorio local</button>");
			$( "#directorys" ).append( "<button id='directory-button' class='btn' onclick='borrar("+ruta+")' ><i class=\"fa fa-trash \"></i>Detener sincronización</button>");
			$( "#directorys" ).append("</div>");
		}else{
			console.log("There was an error")
			alert("Ups!\n" + stderr);
		}
	});
	processes.push(ls);
}

function change_if(){
	interface = $('#interface').val();
	side_color = $('#side_color').val();
	side_text_color = $('#side_action_color').val();
	main_color = $('#main_color').val();
	if (typeof(side_color) != 'undefined' && side_color != null && side_color != ""){
		$('.menu-active').css("background",side_color)
	}
	if (typeof(side_text_color) != 'undefined' && side_text_color != null && side_text_color != ""){
		$('.text').css("color",side_text_color)
	}
	if (typeof(main_color) != 'undefined' && main_color != null && main_color != ""){
		$('.title').css("color",main_color)
		$('#floating-button').css("background",main_color)
	}
}

function delete_changes(){
	side_color = "#556270" ;
	side_text_color = "#dfe5eb";
	main_color = "#FF6B6B";
	$('.menu-active').css("background",side_color)
	$('.text').css("color",side_text_color)
	$('.title').css("color",main_color)
	$('#floating-button').css("background",main_color)
}


function sleep (time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

function shell(ruta)
{
	const spawn = require('child_process').spawn;
	const ls = spawn('nautilus', [ruta]);
}

function eliminar()
{
	var i;
	$( "#eliminar" ).html("");
	for (i = 0; i <directorios.length ; i++) {
		var ruta = '"'+directorios[i] +'"';
		$( "#eliminar" ).append( "<button type='button' onclick='borrar("+ruta+")' class='btn' data-dismiss='modal'>"+directorios[i]+"</button>");
	};
}

function borrar(id)
{
	console.log("Voy a borrar a ");
	console.log(id);
	for (i = 0; i <directorios.length ; i++) {
		if (directorios[i]==id) {
				directorios.splice(i,1);
				processes[i].kill();
		}
	};

	$( "#directorys" ).html("<h3>Administración</h3>");
	for (i = 0; i <directorios.length ; i++) {
		$( "#directorys" ).append( "<p> <i class = \"fa fa-refresh fa-spin\"></i>   "+ directorios[i] + " <br>  <i class = \"fa fa-users\"></i>   " + grupos[i] + " <br>  <i class = \"fa fa-user\"></i>   "  + users[i] + "</p>");
		$( "#directorys" ).append( "<div class='directory' id='"+directorios[i]+"'>");
		var ruta = '"' + directorios[i] +'"';
		$( "#directorys" ).append( "<button id='directory-button' onclick='shell("+ruta+")' class='btn'><i class='fa fa-folder-open-o'></i>Abrir directorio local</button>");
		$( "#directorys" ).append( "<button id='directory-button' class='btn' onclick='borrar("+ruta+")' ><i class=\"fa fa-trash \"></i>Detener sincronización</button>");
		$( "#directorys" ).append("</div>");
	};
}

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

$("#close-set").click(function(){
	$(".main-panel").css("display","block")
	$(".setting-panel").css("display","none")
});

$("#floating-button").click(function(){
    $("body").removeClass('menu-active')
		console.log("new");
		$('#newModal').modal('show');
		//$('.modal-backdrop').remove();
});


/*
  -----------------------------------------Ventana--------------------------------------------
*/
var win =  nw.Window.get();
var maximizado = false;
function close()
{
  win.hide();
	var tray;
	tray = new nw.Tray({ icon: 'icon.png' });
	tray.on('click', function() {
	  win.show();
	  this.remove();
	  tray = null;
	});
}
function close_all()
{
	for (i = 0; i < processes.length ; i++) {
		processes[i].kill();
	}
  win.close();

}
function minimize()
{
  win.minimize();
}
function maximize()
{
  if(maximizado)
  {
    win.unmaximize();
    maximizado=false;
  }else {
    win.maximize();
    maximizado=true;
  }

}

win.on('maximize',function () {
  maximizado=true;
});

/*----------------------------------------------------------------------------------------*/
