window.onload = function () {
    document.getElementById('received-count').textContent = 0;
    let myTable = document.getElementById('ltr-display-tbl');
    myTable.addEventListener('click', handleTableClick);
}

function handleTableClick(event) {
    let total = 0;
    if(event.target.name == 'received_ltr') {
        rcv_ltrs = document.querySelectorAll('.chkbox-rcv');
        for (let i=0; i<rcv_ltrs.length; i++) {
            if (rcv_ltrs[i].checked == true) {
                total ++;
            }
        }
        document.getElementById('received-count').textContent = total;
    }
}

