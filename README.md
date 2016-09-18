Files cluster!
===================


¡Hola!, este programa está diseñado para compartir archivos a través de IPv6 en una **red local** de la manera más sencilla posible. El programa fue diseñado para ser escalable por lo que se escribió el script principal en python y el frontend en node js.

----------


Uso
-------------

##Como script

El script se ejecuta asi:
> **Nota:** Para facilidad de uso solo se indica un nombre de grupo a conectar y a través de ese nombre se genera una dirección multicast donde los scripts en otras computadoras de la red comparten información necesaria para compartir los archivos.

    $ ./write.py -g un_grupo -n username -d /tmp/prueba -i vmnet8

Parámetro     | Descripción
-------- | ---
-g / --group | Grupo a quien se va a compartir el directorio
-n / --name    | Nombre que representa al usuario
-d / --directory     | Directorio a compartir
-i / --interface     | Interfaz de red por compartir

> **Nota:** Por defecto se usa la interfaz de red principal de la computadora, pero se puede escoger con el parámetro -i

##Desde GUI

Desde la interfaz gráfica se selecciona la opción "nuevo directorio" dónde se agrega la información sobre el grupo, nombre de usuario y directorio a compartir.

> **Nota:** Se pueden compartir cualquier cantidad de directorios en la red a diferentes grupos
> El script es un paquete de python por lo que puede modificarse para ser usado en cualquier proyecto



> > **Nota:** Para ejecutar el GUI es necesario instalar NW.js: http://nwjs.io/
Lo que se descargue se agrega en la carpeta /frontend y ejecutamos en linux con el script Linux.sh
