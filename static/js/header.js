$(document).ready(function(){
  $('.collapsible').collapsible()
  $('.dropdown-trigger').dropdown()
  $('.modal').modal()
  $('.tabs').tabs()
  $('.sidenav').sidenav();
  $('.tooltipped').tooltip();
  $('select').formSelect();
  $('.datepicker').datepicker({ 'yearRange': 100, 'format':'mm-dd-yyyy' });
  $('.carousel').carousel();


  $("#profileform").on('submit', postMethodFile);
  $("#loginform").materialvalidation();
  $("#loginform").on('submit', postMethodValidation);
  $("#changepassform").on('submit', postMethod);
  $("#transactionform").materialvalidation();
  $("#transactionform").on('submit', postMethod);

var elem = document.querySelector('.fixed-action-btn');
  var instance = M.FloatingActionButton.init(elem, {
    direction: 'top'
});


  $(".createwallet").on('click',function () {
        $.ajax({
            method: "GET",
            url: $(".createwallet").attr('data-url'),
            success: function(data, textStatus, jqXHR){
              M.toast({html: "Successfully created wallet"})
              location.reload()
            },
            error: function(response){
              console.log(response)
            },
        })
        return false
    });
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function postMethod (evt) {
    evt.preventDefault();
    evt.stopPropagation();
    var $formData = $(this).serialize()
    var $thisURL = $(this).attr('data-url')
    var $redirect = $(this).attr('data-redirect')
    $.ajax({
        method: "POST",
        url: $thisURL,
        data: $formData,
        dataType: "json",
        success: function(data){
          M.toast({html: '<i class="material-icons">check</i>&nbsp;'+ data['message'], classes: 'green rounded'})
          window.location.href = $redirect
          if($('.modal').isOpen == true){
            $('.modal').modal('close');
          }
        },
        error: function(response){
          Object.keys(response.responseJSON).forEach(function(key){
              M.toast({html: '<i class="material-icons">error</i>&nbsp;'+ response.responseJSON[key], classes: 'red rounded'})
            });
        },
    })
    return false
}

function postMethodValidation(evt){
    evt.preventDefault();
    evt.stopPropagation();
    if ($(this).data().materialvalidation.methods.validate()) {
        var $formData = $(this).serialize()
        var $thisURL = $(this).attr('data-url')
        var $redirect = $(this).attr('data-redirect')
        $.ajax({
            method: "POST",
            url: $thisURL,
            data: $formData,
            dataType: "json",
            success: function(data){
              M.toast({html: data['message']})
              window.location.href = $redirect
            },
            error: function(response){
              Object.keys(response.responseJSON).forEach(function(key){
                  M.toast({html: response.responseJSON[key]})
                });
            },
        })
    }
    return false
}

function postMethodFile (evt) {
    evt.preventDefault();
    evt.stopPropagation();

    $form = $(this);
    var formData = new FormData(this);
    var $thisURL = $(this).attr('data-url')
    var $redirect = $(this).attr('data-redirect')
    $.ajax({
        type: 'POST',
        url: $thisURL,
        data: formData,
        success: function(data){
          M.toast({html: '<i class="material-icons">check</i>&nbsp;'+ data['message'], classes: 'green rounded'})
          window.location.href = $redirect
        },
        error: function(response){
          console.log(response)
          Object.keys(response.responseJSON).forEach(function(key){
              M.toast({html: '<i class="material-icons">error</i>&nbsp;'+ response.responseJSON[key], classes: 'red rounded'})
            });
        },
        cache: false,
        contentType: false,
        processData: false
    })
    return false
}