function activeMenuOption(href) {
    $(".app-menu .nav-link")
    .removeClass("active")
    .removeAttr('aria-current')

    $(`[href="${(href ? href : "#/")}"]`)
    .addClass("active")
    .attr("aria-current", "page")
}

const app = angular.module("angularjsApp", ["ngRoute"])
app.config(function ($routeProvider, $locationProvider) {
    $locationProvider.hashPrefix("")

    $routeProvider
    .when("/", {
        templateUrl: "/app",
        controller: "appCtrl"
    })
    .when("/clientes", {
        templateUrl: "/clientes",
        controller: "clientesCtrl"
    })
    .otherwise({
        redirectTo: "/"
    })
})
app.run(["$rootScope", "$location", "$timeout", function($rootScope, $location, $timeout) {
    function actualizarFechaHora() {
        lxFechaHora = DateTime
        .now()
        .setLocale("es")

        $rootScope.angularjsHora = lxFechaHora.toFormat("hh:mm:ss a")
        $timeout(actualizarFechaHora, 1000)
    }

    $rootScope.slide = ""

    actualizarFechaHora()

    $rootScope.$on("$routeChangeSuccess", function (event, current, previous) {
        $("html").css("overflow-x", "hidden")
        
        const path = current.$$route.originalPath

        if (path.indexOf("splash") == -1) {
            const active = $(".app-menu .nav-link.active").parent().index()
            const click  = $(`[href^="#${path}"]`).parent().index()

            if (active != click) {
                $rootScope.slide  = "animate__animated animate__faster animate__slideIn"
                $rootScope.slide += ((active > click) ? "Left" : "Right")
            }

            $timeout(function () {
                $("html").css("overflow-x", "auto")

                $rootScope.slide = ""
            }, 1000)

            activeMenuOption(`#${path}`)
        }
    })
}])

app.controller("appCtrl", function ($scope, $http) {
    $("#frmInicioSesion").submit(function (event) {
        event.preventDefault()
        $.post("iniciarSesion", $(this).serialize(), function (respuesta) {
            if (respuesta.length) {
                alert("Iniciaste Sesión")
                window.location = "/#/productos"

                return
            }

            alert("Usuario y/o Contraseña Incorrecto(s)")
        })
    })
})

app.controller("clientesCtrl", function ($scope, $http) {

    function cargarTablaClientes() {
        $.get("/tbodyClientes", function(html) {
            $("#tbodyClientes").html(html);
        });
    }

    cargarTablaClientes();

    Pusher.logToConsole = true;
    var pusher = new Pusher("bf79fc5f8fe969b1839e", { cluster: "us2" });
    var channel = pusher.subscribe("canalClientes");
    channel.bind("eventoClientes", function(data) {
        cargarTablaClientes();
    });

     $(document).on("click", "#btnBuscarCliente", function() {
        const busqueda = $("#txtBuscarCliente").val().trim();

        if(busqueda === "") {
            cargarTablaClientes();
            return;
        }

        $.get("/clientes/buscar", { busqueda: busqueda }, function(registros) {
            let trsHTML = "";
            registros.forEach(cliente => {
                trsHTML += `
                    <tr>
                        <td>${cliente.idCliente}</td>
                        <td>${cliente.nombreCliente}</td>
                        <td>${cliente.telefono}</td>
                        <td>${cliente.correoElectronico}</td>
                        <td>
                            <button class="btn btn-danger btn-sm btn-eliminar" data-id="${cliente.idCliente}">Eliminar</button>
                        </td>
                    </tr>
                `;
            });
            $("#tbodyClientes").html(trsHTML);
        }).fail(function(xhr){
            console.error("Error al buscar clientes:", xhr.responseText);
        });
    });

    // Permitir Enter en input
    $("#txtBuscarCliente").on("keypress", function(e) {
        if(e.which === 13) {
            $("#btnBuscarCliente").click();
        }
    });

    $(document).on("submit", "#frmCliente", function (event) {
        event.preventDefault();

        const idCliente = $("#idCliente").val(); // Oculto en el form

        $.post("/cliente", {
            idCliente: idCliente,
            nombreCliente: $("#txtNombreCliente").val(),
            telefono: $("#txtTelefono").val(),
            correoElectronico: $("#txtCorreoElectronico").val()
        }, function(response){
            console.log("Cliente guardado o actualizado correctamente");
            $("#frmCliente")[0].reset();
            $("#idCliente").val(""); // limpiar campo oculto
            cargarTablaClientes(); 
        }).fail(function(xhr){
            console.error("Error al guardar/actualizar cliente:", xhr.responseText);
        });

    });

    $(document).on("click", "#tbodyClientes .btn-eliminar", function(){
        const id = $(this).data("id");
        if(confirm("¿Deseas eliminar este cliente?")) {
            $.post("/clientes/eliminar", {id: id}, function(response){
                console.log("Cliente eliminado correctamente");
                cargarTablaClientes(); 
            }).fail(function(xhr){
                console.error("Error al eliminar cliente:", xhr.responseText);
            });
        }
    });
        // ======== BOTÓN EDITAR ========
    $(document).on("click", "#tbodyClientes .btn-editar", function() {
        const id = $(this).data("id");
        const nombre = $(this).data("nombre");
        const telefono = $(this).data("telefono");
        const correo = $(this).data("correo");

        // Rellenar el formulario
        $("#idCliente").val(id);
        $("#txtNombreCliente").val(nombre);
        $("#txtTelefono").val(telefono);
        $("#txtCorreoElectronico").val(correo);

        // Cambiar el texto del botón para indicar que está en modo actualización
        const btnGuardar = $("#btnGuardar");
        btnGuardar.text("Actualizar");
        btnGuardar.removeClass("btn-primary").addClass("btn-success");
    });


});

const DateTime = luxon.DateTime
let lxFechaHora

document.addEventListener("DOMContentLoaded", function (event) {
    const configFechaHora = {
        locale: "es",
        weekNumbers: true,
        // enableTime: true,
        minuteIncrement: 15,
        altInput: true,
        altFormat: "d/F/Y",
        dateFormat: "Y-m-d",
        // time_24hr: false
    }

    activeMenuOption(location.hash)
})






