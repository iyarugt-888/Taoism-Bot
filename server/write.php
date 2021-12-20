<?php
$myfile = fopen("client_settings.json", "w") or die("Unable to open file!");
$txt = $_GET["data"];
fwrite($myfile, $txt);
fclose($myfile);
?>