<?php
$myfile = fopen("client_settings.json", "r") or die("Unable to open file!");
echo fread($myfile,filesize("client_settings.json"));
fclose($myfile);
?>