window.addEventListener("scroll", ()=>{
    const navbar = document.getElementById("navigation")
    const scroll_event = document.querySelector(".gotopdiv") 
    if(document.body.scrollTop > 65 || document.documentElement.scrollTop > 65){
        scroll_event.style.cssText = `display: flex;`
    }else{
        scroll_event.style.cssText = `display: none`
    }
})
function gotop(){
    document.body.scrollTop = 0
    document.documentElement.scrollTop = 0
}

// EyeBall_Password
function eye_ball(){
    var eye_ball = document.getElementById("togglePassword")
    var pw_field = document.querySelectorAll(".pwfield")
    if (eye_ball.innerHTML == "visibility_off"){
        pw_field.forEach(pw => pw.type = "text")
        eye_ball.innerHTML = "visibility"
    }else{
        pw_field.forEach(pw => pw.type = "password")
        eye_ball.innerHTML = "visibility_off"
    }
}

// dropdown
const dropdown = document.querySelector(".cust_dropdown")
dropdown.onclick = function(){
    dropdown.classList.toggle('active')
}
