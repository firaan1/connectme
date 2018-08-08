function ButtonDisplay(sesssionloggedin) {
// check session logged in
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
}

document.addEventListener('DOMContentLoaded', () => {

  

});
