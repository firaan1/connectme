function ButtonDisplay(sesssionloggedin) {
  //
  // localStorage.removeItem('last_channel')
if(sesssionloggedin != "False") {
  const loggedout = document.querySelectorAll('.loggedout');
  loggedout[0].style.display = "none";
  loggedout[1].style.display = "none";
  document.querySelector('.loggedin').style.display = "inline";
} else {
  document.querySelector('.loggedin').style.display = "none";
  const loggedout = document.querySelectorAll('.loggedout');
  loggedout[0].style.display = "inline";
  loggedout[1].style.display = "inline";
}

// button functions
document.querySelectorAll('.btnloc').forEach(
  button => {
    button.onclick = () => {
      localStorage.removeItem('last_channel');
      if(button.dataset.urlfor === "/logout"){
        // localStorage.removeItem('session_logged_in')
        localStorage.clear()
      }
      location.href = location.protocol + '//' + document.domain + ':' + location.port + button.dataset.urlfor
    }
  }
);

}

function datenow(){
  let date = new Date();
  let date_now = date.getFullYear() + "-" + (date.getMonth() + 1) + "-" + date.getDate();
  return date_now
}
