/**
 * Main JS para SparkManagerDocs
 * Controla comportamentos de interface e responsividade
 */

(function ($) {
    "use strict";

    // Spinner de carregamento
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();
    
    
    // Botão Voltar ao Topo
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });


    // Sidebar Toggler (Lógica secundária para garantir compatibilidade com Tailwind)
    $('.sidebar-toggler').click(function () {
        $('.sidebar, .content').toggleClass("open");
        return false;
    });

    /**
     * Lógica de Auto-fechamento da Sidebar (Mobile)
     * Quando o usuário clica em um link na sidebar em modo mobile, ela fecha automaticamente.
     */
    $(document).ready(function() {
        if ($(window).width() < 768) {
            $('.sidebar a').click(function() {
                // Se estiver usando Alpine.js no base.html, acessamos o estado dele
                if (window.Alpine) {
                    // Busca o elemento que contém o x-data da sidebar
                    const sidebarElement = document.querySelector('[x-data]');
                    if (sidebarElement && sidebarElement.__x) {
                        sidebarElement.__x.$data.sidebarOpen = false;
                    }
                }
            });
        }
    });

})(jQuery);