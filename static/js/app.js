    function activeMenuOption(href) {
        $("#appMenu .nav-link")
        .removeClass("active")
        .removeAttr('aria-current')

        $(`[href="${(href ? href : "#/")}"]`)
        .addClass("active")
        .attr("aria-current", "page")
    }

    function disableAll() {
        const elements = document.querySelectorAll(".while-waiting")
        elements.forEach(function (el, index) {
            el.setAttribute("disabled", "true")
            el.classList.add("disabled")
        })
    }

    function enableAll() {
        const elements = document.querySelectorAll(".while-waiting")
        elements.forEach(function (el, index) {
            el.removeAttribute("disabled")
            el.classList.remove("disabled")
        })
    }

    function debounce(fun, delay) {
        let timer
        return function (...args) {
            clearTimeout(timer)
            timer = setTimeout(function () {
                fun.apply(this, args)
            }, delay)
        }
    }

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

    const DateTime = luxon.DateTime
    let lxFechaHora
    let diffMs = 0

    const app = angular.module("angularjsApp", ["ngRoute"])

    app.config(function ($routeProvider, $locationProvider, $provide) {
        $provide.decorator("MensajesService", function ($delegate, $log) {
            const originalModal = $delegate.modal
            const originalPop   = $delegate.pop
            const originalToast = $delegate.toast

            $delegate.modal = function (msg) {
                originalModal(msg, "Mensaje", [
                    {"html": "Aceptar", "class": "btn btn-lg btn-secondary", defaultButton: true, dismiss: true}
                ])
            }
            $delegate.pop = function (msg) {
                $(".div-temporal").remove()
                $("body").prepend($("<div />", {
                    class: "div-temporal"
                }))
                originalPop(".div-temporal", msg, "info")
            }
            $delegate.toast = function (msg) {
                originalToast(msg, 2)
            }

            return $delegate
        })
        
        $locationProvider.hashPrefix("")

        $routeProvider
        .when("/", {
            templateUrl: "/login",
            controller: "loginCtrl"
        })
        .when("/laboratorio", {
            templateUrl: "/laboratorio",
            controller: "laboratorioCtrl"
        })
        .when("/estudiantes", {
            templateUrl: "/estudiantes",
            controller: "estudiantesCtrl"
        })
        .otherwise({
            redirectTo: "/"
        })
    })
    app.run(["$rootScope", "$location", "$timeout", "SesionService", function($rootScope, $location, $timeout, $SesionService) {
        $rootScope.slide             = ""
        $rootScope.spinnerGrow       = false
        $rootScope.sendingRequest    = false
        $rootScope.incompleteRequest = false
        $rootScope.completeRequest   = false
        $rootScope.login             = localStorage.getItem("login")
        const defaultRouteAuth       = "#/laboratorio"
        let timesChangesSuccessRoute = 0


        function actualizarFechaHora() {
            lxFechaHora = DateTime.now().plus({
                milliseconds: diffMs
            })

            // $rootScope.angularjsHora = lxFechaHora.setLocale("es").toFormat("hh:mm:ss a")
            $rootScope.$applyAsync(() => {
                $rootScope.angularjsHora = lxFechaHora.setLocale("es").toFormat("hh:mm:ss a");
            });
            $timeout(actualizarFechaHora, 500)
        }
        actualizarFechaHora()


        let preferencias = localStorage.getItem("preferencias")
        try {
            preferencias = (preferencias ? JSON.parse(preferencias) :  {})
        }
        catch (error) {
            preferencias = {}
        }
        $rootScope.preferencias = preferencias
        $SesionService.setUsuario(preferencias.usuario)
        $SesionService.setTipo(preferencias.tipo)

        $rootScope.$on("$routeChangeSuccess", function (event, current, previous) {
            $rootScope.spinnerGrow = false
            const path             = current.$$route.originalPath


            // AJAX Setup
            $.ajaxSetup({
                beforeSend: function (xhr) {
                    // $rootScope.sendingRequest = true
                },
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("JWT")}`
                },
                error: function (error) {
                    $rootScope.sendingRequest    = false
                    $rootScope.incompleteRequest = false
                    $rootScope.completeRequest   = true

                    const status = error.status
                    enableAll()

                    if (status) {
                        const respuesta = error.responseText
                        console.log("error", respuesta)

                        if (status == 401) {
                            cerrarSesion()
                            return
                        }

                        modal(respuesta, "Error", [
                            {html: "Aceptar", class: "btn btn-lg btn-secondary", defaultButton: true, dismiss: true}
                        ])
                    }
                    else {
                        toast("Error en la petici&oacute;n.")
                        $rootScope.sendingRequest    = false
                        $rootScope.incompleteRequest = true
                        $rootScope.completeRequest   = false
                    }
                },
                statusCode: {
                    200: function (respuesta) {
                        $rootScope.sendingRequest    = false
                        $rootScope.incompleteRequest = false
                        $rootScope.completeRequest   = true
                    },
                    401: function (respuesta) {
                        cerrarSesion()
                    },
                }
            })

            // solo hacer si se carga una ruta existente que no sea el splash
            if (path.indexOf("splash") == -1) {
                // validar login
                function validarRedireccionamiento() {
                    const login = localStorage.getItem("login")

                    if (login) {
                        if (path == "/") {
                            window.location = defaultRouteAuth
                            return
                        }

                        $(".btn-cerrar-sesion").click(function (event) {
                            $.post("cerrarSesion")
                            $timeout(function () {
                                cerrarSesion()
                            }, 500)
                        })
                    }
                    else if ((path != "/")
                        &&  (path.indexOf("emailToken") == -1)
                        &&  (path.indexOf("resetPassToken") == -1)) {
                        window.location = "#/"
                    }
                }
                function cerrarSesion() {
                    localStorage.removeItem("JWT")
                    localStorage.removeItem("login")
                    localStorage.removeItem("preferencias")

                    const login      = localStorage.getItem("login")
                    let preferencias = localStorage.getItem("preferencias")

                    try {
                        preferencias = (preferencias ? JSON.parse(preferencias) :  {})
                    }
                    catch (error) {
                        preferencias = {}
                    }

                    $rootScope.redireccionar(login, preferencias)
                }
                $rootScope.redireccionar = function (login, preferencias) {
                    $rootScope.login        = login
                    $rootScope.preferencias = preferencias

                    validarRedireccionamiento()
                }
                validarRedireccionamiento()


                // animate.css
                const active = $("#appMenu .nav-link.active").parent().index()
                const click  = $(`[href^="#${path}"]`).parent().index()

                if ((active <= 0)
                ||  (click  <= 0)
                ||  (active == click)) {
                    $rootScope.slide = "animate__animated animate__faster animate__bounceIn"
                }
                else if (active != click) {
                    $rootScope.slide  = "animate__animated animate__faster animate__slideIn"
                    $rootScope.slide += ((active > click) ? "Left" : "Right")
                }


                // swipe
                if (path.indexOf("rentas") != -1) {
                    $rootScope.leftView      = ""
                    $rootScope.rightView     = "clientes"
                    $rootScope.leftViewLink  = ""
                    $rootScope.rightViewLink = "#/clientes"
                }
                else if (path.indexOf("clientes") != -1) {
                    $rootScope.leftView      = "rentas"
                    $rootScope.rightView     = "trajes"
                    $rootScope.leftViewLink  = "#/rentas"
                    $rootScope.rightViewLink = "#/trajes"
                }
                else if (path.indexOf("ventas") != -1) {
                    $rootScope.leftView      = "clientes"
                    $rootScope.rightView     = ""
                    $rootScope.leftViewLink  = "#/clientes"
                    $rootScope.rightViewLink = ""
                }
                else {
                    $rootScope.leftView      = ""
                    $rootScope.rightView     = ""
                    $rootScope.leftViewLink  = ""
                    $rootScope.rightViewLink = ""
                }

                let offsetX
                let threshold
                let startX = 0
                let startY = 0
                let currentX = 0
                let isDragging = false
                let isScrolling = false
                let moved = false
                let minDrag = 5

                function resetDrag() {
                    offsetX = -window.innerWidth
                    threshold = window.innerWidth / 4
                    $("#appSwipeWrapper").get(0).style.transition = "transform 0s ease"
                    $("#appSwipeWrapper").get(0).style.transform = `translateX(${offsetX}px)`
                }
                function startDrag(event) {
                    if (isScrolling && isPartiallyVisible($("#appContent").get(0))) {
                        resetDrag()
                    }

                    isDragging  = true
                    moved       = false
                    isScrolling = false

                    startX = getX(event)
                    startY = getY(event)

                    $("#appSwipeWrapper").get(0).style.transition = "none"
                    document.body.style.userSelect = "none"
                }
                function onDrag(event) {
                    if (!isDragging
                    ||  $(event.target).parents("table").length
                    ||  $(event.target).parents("button").length
                    ||  $(event.target).parents("span").length
                    ||   (event.target.nodeName == "BUTTON")
                    ||   (event.target.nodeName == "SPAN")
                    || $(event.target).parents(".plotly-grafica").length
                    || $(event.target).hasClass("plotly-grafica")) {
                        return
                    }

                    let x = getX(event)
                    let y = getY(event)

                    let deltaX = x - startX
                    let deltaY = y - startY
                    
                    if (isScrolling) {
                        if (isPartiallyVisible($("#appContent").get(0))) {
                            resetDrag()
                        }
                        return
                    }

                    if (!moved) {
                        if (Math.abs(deltaY) > Math.abs(deltaX)) {
                            isScrolling = true
                            return
                        }
                    }

                    if (Math.abs(deltaX) > minDrag) {
                        moved = true
                    }

                    currentX = offsetX + deltaX
                    $("#appSwipeWrapper").get(0).style.transform = `translateX(${currentX}px)`
                    $("#appSwipeWrapper").get(0).style.cursor = "grabbing"

                    event.preventDefault()
                }
                function isVisible(element) {
                    const rect = element.getBoundingClientRect()
                    return rect.left >= 0 && rect.right <= window.innerWidth
                }
                function isPartiallyVisible(element) {
                    const rect = element.getBoundingClientRect()
                    return rect.right > 0 && rect.left < window.innerWidth
                }
                function endDrag() {
                    if (!isDragging) {
                        return
                    }
                    $("#appSwipeWrapper").get(0).style.cursor = "grab"
                    isDragging = false
                    document.body.style.userSelect = ""
                    if (isScrolling) {
                        if (isPartiallyVisible($("#appContent").get(0))) {
                            resetDrag()
                        }
                        return
                    }

                    if (!moved) {
                        $("#appSwipeWrapper").get(0).style.transition = "transform 0.3s ease"
                        $("#appSwipeWrapper").get(0).style.transform = `translateX(${offsetX}px)`
                        return
                    }

                    let delta = currentX - offsetX
                    let finalX = offsetX

                    let href, visible

                    if (delta > threshold && offsetX < 0) {
                        finalX = offsetX + window.innerWidth
                        $("#appContentLeft").css("visibility", "visible")
                        $("#appContentRight").css("visibility", "hidden")
                        href = $("#appContentLeft").children("div").eq(0).attr("data-href")
                        visible = isPartiallyVisible($("#appContentLeft").get(0))
                    } else if (delta < -threshold && offsetX > -2 * window.innerWidth) {
                        finalX = offsetX - window.innerWidth
                        $("#appContentLeft").css("visibility", "hidden")
                        $("#appContentRight").css("visibility", "visible")
                        href = $("#appContentRight").children("div").eq(0).attr("data-href")
                        visible = isPartiallyVisible($("#appContentRight").get(0))
                    }

                    if (href && visible) {
                        resetDrag()
                        $timeout(function () {
                            window.location = href
                        }, 100)
                    } else if (!href) {
                        resetDrag()
                        return
                    }

                    $("#appSwipeWrapper").get(0).style.transition = "transform 0.3s ease"
                    $("#appSwipeWrapper").get(0).style.transform = `translateX(${finalX}px)`
                    offsetX = finalX
                }
                function getX(event) {
                    return event.touches ? event.touches[0].clientX : event.clientX
                }
                function getY(event) {
                    return event.touches ? event.touches[0].clientY : event.clientY
                }
                function completeScreen() {
                    $(".div-to-complete-screen").css("height", 0)
                    const altoHtml    = document.documentElement.getBoundingClientRect().height
                    const altoVisible = document.documentElement.clientHeight
                    $(".div-to-complete-screen").css("height", ((altoHtml < altoVisible)
                    ? (altoVisible - altoHtml)
                    : 0) + (16 * 4))
                }

                $(document).off("mousedown touchstart mousemove touchmove click", "#appSwipeWrapper")

                $(document).on("mousedown",  "#appSwipeWrapper", startDrag)
                $(document).on("touchstart", "#appSwipeWrapper", startDrag)
                $(document).on("mousemove",  "#appSwipeWrapper", onDrag)
                // $(document).on("touchmove",  "#appSwipeWrapper", onDrag)
                document.querySelector("#appSwipeWrapper").addEventListener("touchmove", onDrag, {
                    passive: false
                })
                $(document).on("mouseup",    "#appSwipeWrapper", endDrag)
                $(document).on("mouseleave", "#appSwipeWrapper", endDrag)
                $(document).on("touchend",   "#appSwipeWrapper", endDrag)
                $(document).on("click",      "#appSwipeWrapper", function (event) {
                    if (moved) {
                        event.stopImmediatePropagation()
                        event.preventDefault()
                        return false
                    }
                })
                $(window).on("resize", function (event) {
                    resetDrag()
                    completeScreen()
                })

                resetDrag()


                // solo hacer una vez cargada la animación
                $timeout(function () {
                    // animate.css
                    $rootScope.slide = ""


                    // swipe
                    completeScreen()


                    // solo hacer al cargar la página por primera vez
                    if (timesChangesSuccessRoute == 0) {
                        timesChangesSuccessRoute++
                        

                        // JQuery Validate
                        $.extend($.validator.messages, {
                            required: "Llena este campo",
                            number: "Solo números",
                            digits: "Solo números enteros",
                            min: $.validator.format("No valores menores a {0}"),
                            max: $.validator.format("No valores mayores a {0}"),
                            minlength: $.validator.format("Mínimo {0} caracteres"),
                            maxlength: $.validator.format("Máximo {0} caracteres"),
                            rangelength: $.validator.format("Solo {0} caracteres"),
                            equalTo: "El texto de este campo no coincide con el anterior",
                            date: "Ingresa fechas validas",
                            email: "Ingresa un correo electrónico valido"
                        })


                        // gets
                        const startTimeRequest = Date.now()
                        $.get("fechaHora", function (fechaHora) {
                            const endTimeRequest = Date.now()
                            const rtt            = endTimeRequest - startTimeRequest
                            const delay          = rtt / 2

                            const lxFechaHoraServidor = DateTime.fromFormat(fechaHora, "yyyy-MM-dd hh:mm:ss")
                            // const fecha = lxFechaHoraServidor.toFormat("dd/MM/yyyy hh:mm:ss")
                            const lxLocal = luxon.DateTime.fromMillis(endTimeRequest - delay)

                            diffMs = lxFechaHoraServidor.toMillis() - lxLocal.toMillis()
                        })

                        $.get("preferencias", {
                            token: localStorage.getItem("fbt")
                        }, function (respuesta) {
                            if (typeof respuesta != "object") {
                                return
                            }

                            console.log("✅ Respuesta recibida:", respuesta)

                            const login      = "1"
                            let preferencias = respuesta

                            localStorage.setItem("login", login)
                            localStorage.setItem("preferencias", JSON.stringify(preferencias))
                            $rootScope.redireccionar(login, preferencias)
                        })


                        // events
                        $(document).on("click", ".toggle-password", function (event) {
                            const prev = $(this).parent().find("input")

                            if (prev.prop("disabled")) {
                                return
                            }

                            prev.focus()

                            if ("selectionStart" in prev.get(0)){
                                $timeout(function () {
                                    prev.get(0).selectionStart = prev.val().length
                                    prev.get(0).selectionEnd   = prev.val().length
                                }, 0)
                            }

                            if (prev.attr("type") == "password") {
                                $(this).children().first()
                                .removeClass("bi-eye")
                                .addClass("bi-eye-slash")
                                prev.attr({
                                    "type": "text",
                                    "autocomplete": "off",
                                    "data-autocomplete": prev.attr("autocomplete")
                                })
                                return
                            }

                            $(this).children().first()
                            .addClass("bi-eye")
                            .removeClass("bi-eye-slash")
                            prev.attr({
                                "type": "password",
                                "autocomplete": prev.attr("data-autocomplete")
                            })
                        })
                    }
                }, 500)

                activeMenuOption(`#${path}`)
            }
        })
    }])

    app.controller("loginCtrl", function ($scope, $http, $rootScope) {
        $rootScope.currentView = ''
        $("#frmInicioSesion").submit(function (event) {
            event.preventDefault()

            pop(".div-inicio-sesion", 'ℹ️Iniciando sesi&oacute;n, espere un momento...', "primary")

            $.post("iniciarSesion", $(this).serialize(), function (respuesta) {
                enableAll()

                if (respuesta.length) {
                    localStorage.setItem("login", "1")
                    localStorage.setItem("preferencias", JSON.stringify(respuesta[0]))
                    $("#frmInicioSesion").get(0).reset()
                    location.reload()
                    return
                }

                pop(".div-inicio-sesion", "Usuario y/o contrase&ntilde;a incorrecto(s)", "danger")
            })

            disableAll()
        })
    })

    app.service("SesionService", function() {
        this.usuario = null
        this.tipo = null

        this.setUsuario = function(usuario) {
            this.usuario = usuario;
        };
        this.getUsuario = function() {
            return this.usuario;
        };

        this.setTipo = function(tipo) {
            this.tipo = tipo;
        };
        this.getTipo = function() {
            return this.tipo;
        };
    });

    app.factory("CategoriaFactory", function () {
        function Categoria(titulo, laboratorio) {
            this.titulo = titulo
            this.laboratorio = laboratorio
        }

        Categoria.prototype.getInfo = function () {
            return {
                titulo: this.titulo,
                laboratorio: this.laboratorio
            }
        }

        return {
            create: function (titulo, laboratorio) {
                return new Categoria(titulo, laboratorio)
            }
        }
    })

    app.service("MensajesService", function () {
        this.modal = modal
        this.pop   = pop
        this.toast = toast
    })

    app.service("HoraAPI", function($q) {
        this.obtenerHoras = function(id) {
            var deferred = $q.defer();

            $.get(`/laboratorio/${id}`) // tu endpoint Flask
            .done(function(horas) {
                deferred.resolve(horas);
            })
            .fail(function(error) {
                deferred.reject(error);
            });

            return deferred.promise;
        };
    });

    app.service("CategoriaAPI", function($q) {
        this.obtenerCategorias = function(categoria) {
            var deferred = $q.defer();

            $.get(`/laboratorio/categorias?categoria=${categoria}`) // si tuvieras endpoint /categorias
            .done(function(categorias) {
                deferred.resolve(categorias);
            })
            .fail(function(error) {
                deferred.reject(error);
            });

            return deferred.promise;
        };
    });

    app.factory("LaboratorioFacade", function(HoraAPI, CategoriaAPI, $q) {
        return {
            obtenerDatosLaboratorio: function(id, categoria) {
                return $q.all({
                    horas: HoraAPI.obtenerHoras(id),
                    categorias: CategoriaAPI.obtenerCategorias(categoria)
                });
            }
        };
    });

    app.controller("laboratorioCtrl", function ($scope, SesionService, CategoriaFactory, MensajesService, LaboratorioFacade) {
        $scope.SesionService = SesionService;
        // Función para cargar todas las horas
        function cargarHoras() {
            $.get("/tbodylaboratorio", function(trsHTML){
                $("#tbodylaboratorio").html(trsHTML)
            })
        }

        cargarHoras()

        $.get("laboratorio/categorias", {
            categoria: "AM"
        },function (am){
            const categoriaAM = CategoriaFactory.create("AM",am)
            console.log("AM Factory", categoriaAM.getInfo())
            $scope.categoriaAM = categoriaAM
        })
        $.get("laboratorio/categorias", {
            categoria: "PM"
        },function (pm){
            const categoriaPM = CategoriaFactory.create("PM",pm)
            console.log("PM Factory", categoriaPM.getInfo())
            $scope.categoriaPM = categoriaPM
        })

        Pusher.logToConsole = true
        var pusher = new Pusher("b51b00ad61c8006b2e6f", {
        cluster: "us2"
        })
        var channel = pusher.subscribe("canallaboratorio")
        channel.bind("eventolaboratorio", function(data) {
            cargarHoras()
        })


        // Buscar 
        $(document).on("click", "#btnBuscarHora", function() {
            const busqueda = $("#txtBuscarHora").val().trim();

            if (busqueda === "") {
                cargarHoras();
                return;
            }

            $.get("/laboratorio/buscar", { busqueda: busqueda }, function(registros) {
                let trsHTML = "";
                registros.forEach(hora => {
                    trsHTML += `
                        <tr>
                            <td>${hora.Id_Hora}</td>
                            <td>${hora.Hora}</td>
                            <td>${hora.Categoria}</td>
                            <td>
                                <button class="btn btn-success btn-sm btn-editar" 
                                    data-id="${hora.Id_Hora}" 
                                    data-hora="${hora.Hora}" 
                                    data-categoria="${hora.Categoria}">
                                    Editar
                                </button>
                                <button class="btn btn-danger btn-sm btn-eliminar" 
                                    data-id="${hora.Id_Hora}">
                                    Eliminar
                                </button>
                            </td>
                        </tr>
                    `;
                });
                $("#tbodylaboratorio").html(trsHTML);
            }).fail(function(xhr) {
                console.error("Error al buscar horas:", xhr.responseText);
            });
        });

        // Permitir Enter para buscar
        $("#txtBuscarHora").on("keypress", function(e) {
            if (e.which === 13) {
                $("#btnBuscarHora").click();
            }
        });

        // Agregar o actualizar una hora
        $(document).on("submit", "#frmLaboratorio", function(event) {
            event.preventDefault();

            // const Id_Hora = $("#idHora").val(); 

            // $.post("/laboratorios", {
            //     Id_Hora: Id_Hora,
            //     Hora: $("#txtHora").val(),
            //     Categoria: $("#txtCategoria").val()
            // }, function(response) {
            //     console.log("Hora guardada o actualizada correctamente");
            //     $("#frmLaboratorio")[0].reset();
            //     $("#idHora").val(""); // limpiar id oculto
            //     cargarHoras();

            //     const btnGuardar = $("#btnGuardar");
            //     btnGuardar.text("Guardar");
            //     btnGuardar.removeClass("btn-success").addClass("btn-primary");
            // }).fail(function(xhr) {
            //     console.error("Error al guardar/actualizar hora:", xhr.responseText);
            // }); 
            const formData = new FormData(this);
            
            $.ajax({
                url: "/laboratorios",
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    MensajesService.toast("Has agregado un horario.")
                    $("#frmLaboratorio")[0].reset();
                    $("#idHora").val("");
                    cargarHoras();

                    const btnGuardar = $("#btnGuardar");
                    btnGuardar.text("Guardar");
                    btnGuardar.removeClass("btn-success").addClass("btn-primary");
                },
                error: function(xhr) {
                    console.error("❌ Error al guardar/actualizar hora:", xhr.responseText);
                }
            });
        });

        $(document).on("click", ".btn-ver-laboratorio", function() {
        const id = $(this).data("id");
        const categoria = $(this).data("categoria");

        LaboratorioFacade.obtenerDatosLaboratorio(id, categoria).then(function (datos) {
            console.log("Horas:", datos.horas);
            console.log("Categorías:", datos.categorias);

            let horas = datos.horas; // array de horas
            let categorias = datos.categorias; // array de categorías

            let laboratorio = horas[0];
            
            let html = `
                <b>ID:</b> ${laboratorio.Id_Hora}<br>
                <b>Hora:</b> ${laboratorio.Hora}<br>
                <b>Categoría:</b> ${laboratorio.Categoria}<br>
                <hr>
                <h5>Horario:</h5>
                <table class="table table-sm table-bordered">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Hora</th>
                            <th>Categoría</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            for (let i in datos.horas) {
                const hora = datos.horas[i];
                html += `
                    <tr>
                        <td>${parseInt(i) + 1}</td>
                        <td>${hora.Hora}</td>
                        <td>${hora.Categoria}</td>
                    </tr>
                `;
            }

            html += `
                    </tbody>
                </table>
            `;

            // Si tienes un modal de mensajes como el del profe:
            MensajesService.modal(html);

            // O si solo quieres mostrarlo en un contenedor:
            // $("#detalleLaboratorio").html(html);
        })
        .catch(function (error) {
            console.error("Error al obtener el laboratorio:", error);
        })
        })

        // Eliminar una hora
        $(document).on("click", "#tbodylaboratorio .btn-eliminar", function() {
            const id = $(this).data("id");
            if (confirm("¿Deseas eliminar esta hora?")) {
                $.post("/horas/eliminar", { id: id }, function(response) {
                    console.log("Hora eliminada correctamente");
                    cargarHoras();
                }).fail(function(xhr) {
                    console.error("Error al eliminar hora:", xhr.responseText);
                });
            }
        });

        // Editar hora
        $(document).on("click", "#tbodylaboratorio .btn-editar", function() {
            const id = $(this).data("id");
            const hora = $(this).data("hora");
            const categoria = $(this).data("categoria");

            $("#idHora").val(id);
            $("#txtHora").val(hora);
            $("#txtCategoria").val(categoria);

            const btnGuardar = $("#btnGuardar");
            btnGuardar.text("Actualizar");
            btnGuardar.removeClass("btn-primary").addClass("btn-success");
        });
        
        

    })

    // ============ ADAPTER PARA ESTUDIANTES ============

    function EstudianteAdapter(estudiante) {
        this.estudiante = estudiante;
    }

    EstudianteAdapter.prototype.toRowHTML = function() {
        const e = this.estudiante;
        return `
            <tr>
                <td>${e.Id_Estudiante}</td>
                <td>${e.Nombre}</td>
                <td>${e.Matricula}</td>
                <td>${e.Carrera}</td>
                <td>${e.Correo}</td>
                <td>${e.Telefono}</td>
                <td>
                    <div class="btn-group" role="group" aria-label="Acciones">
                        <button class="btn btn-danger btn-sm btn-eliminar" data-id="${e.Id_Estudiante}">Eliminar</button>
                        <button class="btn btn-warning btn-sm btn-modificar" data-id="${e.Id_Estudiante}">Modificar</button>
                    </div>
                </td>
            </tr>
        `;
    };

    function renderEstudiantesTabla(listaEstudiantes) {
        let trsHTML = "";
        listaEstudiantes.forEach(function(e) {
            const adapter = new EstudianteAdapter(e);
            trsHTML += adapter.toRowHTML();
        });

        $("#tbodyEstudiantes").html(trsHTML);

        // Actualizar el total en el input
        $("#totalEstudiantes").val(listaEstudiantes.length);
    }

    app.controller("estudiantesCtrl", function ($scope, MensajesService) {

    // Cargar estudiantes (usa JSON + Adapter)
    function cargarEstudiantes() {
        $.get("/tbodyEstudiantes", function(registros){
            renderEstudiantesTabla(registros);
        }).fail(function(xhr) {
            console.error("❌ Error al cargar estudiantes:", xhr.responseText);
        });
    }

    cargarEstudiantes();

    // Pusher: para actualizaciones en tiempo real
    Pusher.logToConsole = true;
    var pusher = new Pusher("b51b00ad61c8006b2e6f", {
        cluster: "us2"
    });
    var channel = pusher.subscribe("canalestudiantes");
    channel.bind("eventoestudiantes", function(data) {
        cargarEstudiantes();
    });

    // Buscar estudiantes (JSON + Adapter)
    $(document).on("click", "#btnBuscarMatricula", function() {
        const busqueda = $("#txtBuscarMatricula").val().trim();

        if (busqueda === "") {
            cargarEstudiantes();
            return;
        }

        $.get("/estudiantes/buscar", { busqueda: busqueda }, function(registros) {
            renderEstudiantesTabla(registros);
        }).fail(function(xhr) {
            console.error("❌ Error al buscar estudiantes:", xhr.responseText);
        });
    });

    $("#txtBuscarMatricula").on("keypress", function(e) {
        if (e.which === 13) {
            $("#btnBuscarMatricula").click();
        }
    });

    // Log de búsquedas (tu observer)
    $scope.$watch("busqueda", function(newVal, oldVal) {
        if (newVal != oldVal) {
            $.get("log", {
                actividad: "Búsqueda de estudiantes",
                descripcion: `Se realizo una búsqueda de estudiantes "${newVal}"`
            });
        }
    });

    // Guardar / actualizar estudiante
    $(document).on("submit", "#frmEstudiantes", function(event) {
        event.preventDefault();

        const formData = new FormData(this);

        $.ajax({
            url: "/estudiantes",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                MensajesService.toast("Has agregado un estudiante.");
                $("#frmEstudiantes")[0].reset();
                $("#IdEstudiante").val("");
                cargarEstudiantes();

                const btnGuardar = $("#btnGuardar");
                btnGuardar.text("Guardar");
                btnGuardar.removeClass("btn-success").addClass("btn-primary");
            },
            error: function(xhr) {
                console.error("❌ Error al guardar/actualizar:", xhr.responseText);
            }
        });
    });

    // Eliminar estudiante
    $(document).on("click", "#tbodyEstudiantes .btn-eliminar", function() {
        const id = $(this).data("id");
        if (confirm("¿Deseas eliminar este estudiante?")) {
            $.post("/estudiantes/eliminar", { IdEstudiante: id }, function(response) {
                console.log("Estudiante eliminado correctamente");
                cargarEstudiantes();
            }).fail(function(xhr) {
                console.error("Error al eliminar estudiante:", xhr.responseText);
            });
        }
    });

    // Modificar estudiante (cargar datos al formulario)
    $(document).on("click", "#tbodyEstudiantes .btn-modificar", function() {
        const id = $(this).data("id");

        $.get(`/estudiantes/${id}`, function(respuesta) {
            if (respuesta.length) {
                const e = respuesta[0];
                $("#IdEstudiante").val(e.Id_Estudiante);
                $("#txtNombre").val(e.Nombre);
                $("#txtMatricula").val(e.Matricula);
                $("#txtCarrera").val(e.Carrera);
                $("#txtCorreo").val(e.Correo);
                $("#txtTelefono").val(e.Telefono);

                const btnGuardar = $("#btnGuardar");
                btnGuardar.text("Actualizar");
                btnGuardar.removeClass("btn-primary").addClass("btn-success");
            }
        }).fail(function(xhr) {
            console.error("❌ Error al obtener estudiante para modificar:", xhr.responseText);
        });
    });

});

    document.addEventListener("DOMContentLoaded", function (event) {
        activeMenuOption(location.hash)
    })
