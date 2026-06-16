const steps = document.querySelectorAll(".step");
const nextBtns = document.querySelectorAll(".next");
const prevBtns = document.querySelectorAll(".prev");

let currentStep = 0;

function toggleBankValidation() {
    const type = document.getElementById('domainType').value;
    console.log("Selected Type:", type); // ✅ DEBUG

    const fields = [
        'bankName','branchName','accountNo','accountType','ifsc','micr'
    ];

    fields.forEach(id => {
        const field = document.getElementById(id);
        if (!field) return;

        if (type === 'Vendor') {
            field.required = true;
        } else {
            field.required = false;
        }
    });
}
function showStep(step){
    steps.forEach((s,index)=>{
        s.classList.remove("active");
        if(index === step){
            s.classList.add("active");
        }
    });
}

function validateStep(step){

    const inputs = steps[step].querySelectorAll("input, select");

    for(let input of inputs){
        if(!input.checkValidity()){
            input.reportValidity();
            return false;
        }
    }

    return true;
}

nextBtns.forEach(btn=>{
    btn.addEventListener("click", ()=>{

        if(validateStep(currentStep)){

            if(currentStep < steps.length - 1){
                currentStep++;
                showStep(currentStep);
            }

        }

    });
});

prevBtns.forEach(btn=>{
    btn.addEventListener("click", ()=>{

        if(currentStep > 0){
            currentStep--;
            showStep(currentStep);
        }


    });
});

