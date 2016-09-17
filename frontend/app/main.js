var win =  nw.Window.get();
var maximizado = false;
function close()
{
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
