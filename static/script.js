document.querySelectorAll(".card").forEach(card=>{

card.addEventListener("mouseenter",()=>{

card.style.scale="1.05";

});

card.addEventListener("mouseleave",()=>{

card.style.scale="1";

});

});
