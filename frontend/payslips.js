// ============================================================
// PAYSLIPS FRONTEND MODULE
// ============================================================
// Employee Payslips
// View + Print / Save PDF
// Provident Fund + Insurance + Other Deduction
// ============================================================

(function () {

    "use strict";

    let currentPayslips = [];
    let currentEmployeeName = "Employee";


    // =========================================================
    // NUMBER
    // =========================================================

    function toNumber(value) {

        const number = Number(value);

        return Number.isFinite(number)
            ? number
            : 0;
    }


    // =========================================================
    // MONEY FORMAT
    // =========================================================

    function formatAmount(value) {

        return toNumber(value).toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }


    // =========================================================
    // ESCAPE HTML
    // =========================================================

    function escapeHtml(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    // =========================================================
    // EMPLOYEE NAME
    // =========================================================

    function resolveEmployeeName(employeeName) {

        const candidates = [

            employeeName,

            currentEmployeeName,

            document.getElementById("accountName")?.value,

            document.getElementById("accountEmployeeName")?.value,

            document.getElementById("employeeName")?.value,

            document.getElementById("accountUsername")?.value

        ];

        for (const candidate of candidates) {

            const value = String(candidate ?? "").trim();

            if (
                value &&
                value.toLowerCase() !== "employee" &&
                value.toLowerCase() !== "undefined" &&
                value.toLowerCase() !== "null"
            ) {
                return value;
            }
        }

        return "Employee";
    }


    // =========================================================
    // NORMALIZE PAYSLIP
    // =========================================================

    // =========================================================
// NORMALIZE PAYSLIP
// =========================================================

function normalizePayslip(payslip) {

    payslip = payslip || {};

    // =====================================================
    // GROSS SALARY
    // =====================================================

    const grossSalary = toNumber(
        payslip.gross_salary ??
        payslip.gross ??
        payslip.salary ??
        0
    );


    // =====================================================
    // PROVIDENT FUND
    // =====================================================

    let providentFund = toNumber(
        payslip.provident_fund ??
        payslip.providentFund ??
        payslip.pf ??
        0
    );


    // =====================================================
    // INSURANCE
    // =====================================================

    let insurance = toNumber(
        payslip.insurance ??
        0
    );


    // =====================================================
    // OTHER DEDUCTION
    // =====================================================

    let otherDeduction = toNumber(
        payslip.other_deduction ??
        payslip.other_deductions ??
        payslip.otherDeduction ??
        0
    );


    // =====================================================
    // OLD DEDUCTION COMPATIBILITY
    //
    // Supports old payslip records such as:
    //
    // {
    //     "gross_salary": 45000,
    //     "deductions": 5000
    // }
    //
    // If individual deduction fields are not available,
    // split the old total into the displayed components.
    // =====================================================

    const oldDeductions = toNumber(
        payslip.deductions ??
        payslip.deduction ??
        payslip.total_deductions ??
        0
    );


    const componentDeductions =
        providentFund +
        insurance +
        otherDeduction;


    // =====================================================
    // BACKWARD COMPATIBILITY
    // =====================================================

    if (
        oldDeductions > 0 &&
        componentDeductions === 0
    ) {

        // PF component
        providentFund = Math.min(
            1800,
            oldDeductions
        );


        // Insurance component
        insurance = Math.min(
            500,
            Math.max(
                0,
                oldDeductions - providentFund
            )
        );


        // Remaining amount
        // becomes Other Deduction
        otherDeduction = Math.max(
            0,
            oldDeductions -
            providentFund -
            insurance
        );
    }


    // =====================================================
    // TOTAL DEDUCTIONS
    // =====================================================

    const totalDeductions =
        providentFund +
        insurance +
        otherDeduction;


    // =====================================================
    // NET SALARY
    //
    // Always calculate from Gross Salary - Deductions.
    // This prevents an old/stale net_salary value from
    // showing an incorrect amount.
    // =====================================================

    const netSalary =
        grossSalary -
        totalDeductions;


    // =====================================================
    // RETURN NORMALIZED PAYSLIP
    // =====================================================

    return {

        month:
            payslip.month ??
            payslip.period ??
            payslip.pay_period ??
            "-",


        gross_salary:
            grossSalary,


        provident_fund:
            providentFund,


        insurance:
            insurance,


        other_deduction:
            otherDeduction,


        deductions:
            totalDeductions,


        net_salary:
            netSalary
    };
}


    // =========================================================
    // STORE PAYSLIPS
    // =========================================================

    function setPayslips(payslips) {

        currentPayslips =
            Array.isArray(payslips)
                ? payslips.map(normalizePayslip)
                : [];


        /*
         * Keep global copy.
         * This helps View/PDF buttons retain the data.
         */

        window.__currentPayslips =
            currentPayslips;
    }


    // =========================================================
    // GET PAYSLIP
    // =========================================================

    function getPayslip(index) {

        const numericIndex = Number(index);


        if (
            !Array.isArray(currentPayslips) ||
            currentPayslips.length === 0
        ) {

            if (
                Array.isArray(
                    window.__currentPayslips
                )
            ) {

                currentPayslips =
                    window.__currentPayslips;
            }
        }


        if (
            !Number.isInteger(numericIndex) ||
            numericIndex < 0 ||
            numericIndex >= currentPayslips.length
        ) {

            return null;
        }


        return normalizePayslip(
            currentPayslips[numericIndex]
        );
    }


    // =========================================================
    // PAYSLIP HTML
    // =========================================================

    function createPayslipHtml(
        payslip,
        employeeName
    ) {

        const data =
            normalizePayslip(payslip);


        const name =
            resolveEmployeeName(employeeName);


        return `

            <div class="payslip-document">

                <div class="payslip-header">

                    <h1>
                        WORKFORCE MANAGEMENT PLATFORM
                    </h1>

                    <h2>
                        EMPLOYEE PAYSLIP
                    </h2>

                </div>


                <div class="payslip-details">

                    <div class="payslip-detail">

                        <strong>
                            Employee Name
                        </strong>

                        <span>
                            ${escapeHtml(name)}
                        </span>

                    </div>


                    <div class="payslip-detail">

                        <strong>
                            Pay Period
                        </strong>

                        <span>
                            ${escapeHtml(data.month)}
                        </span>

                    </div>

                </div>


                <table class="payslip-document-table">

                    <thead>

                        <tr>

                            <th>
                                Description
                            </th>

                            <th>
                                Amount
                            </th>

                        </tr>

                    </thead>


                    <tbody>

                        <tr>

                            <td>
                                Gross Salary
                            </td>

                            <td class="amount">
                                ₹${formatAmount(
                                    data.gross_salary
                                )}
                            </td>

                        </tr>


                        <tr>

                            <td>
                                Provident Fund
                            </td>

                            <td class="amount">
                                ₹${formatAmount(
                                    data.provident_fund
                                )}
                            </td>

                        </tr>


                        <tr>

                            <td>
                                Insurance
                            </td>

                            <td class="amount">
                                ₹${formatAmount(
                                    data.insurance
                                )}
                            </td>

                        </tr>


                        <tr>

                            <td>
                                Other Deduction
                            </td>

                            <td class="amount">
                                ₹${formatAmount(
                                    data.other_deduction
                                )}
                            </td>

                        </tr>


                        <tr class="total-deduction-row">

                            <td>
                                <strong>
                                    Total Deductions
                                </strong>
                            </td>

                            <td class="amount">

                                <strong>
                                    ₹${formatAmount(
                                        data.deductions
                                    )}
                                </strong>

                            </td>

                        </tr>


                        <tr class="net-row">

                            <td>
                                <strong>
                                    Net Salary
                                </strong>
                            </td>

                            <td class="amount">

                                <strong>
                                    ₹${formatAmount(
                                        data.net_salary
                                    )}
                                </strong>

                            </td>

                        </tr>

                    </tbody>

                </table>


                <div class="payslip-footer">

                    <p>
                        Gross Salary - Total Deductions = Net Salary
                    </p>

                    <p>
                        This is a computer-generated payslip.
                    </p>

                </div>

            </div>

        `;
    }


    // =========================================================
    // CSS
    // =========================================================

    function addStyles() {

        if (
            document.getElementById(
                "payslip-module-styles"
            )
        ) {
            return;
        }


        const style =
            document.createElement("style");


        style.id =
            "payslip-module-styles";


        style.textContent = `

            .payslip-modal {

                position: fixed;

                inset: 0;

                z-index: 99999;

                background:
                    rgba(0, 0, 0, 0.75);

                display: none;

                align-items: center;

                justify-content: center;

                padding: 20px;
            }


            .payslip-modal.active {

                display: flex;
            }


            .payslip-modal-box {

                width: min(900px, 96vw);

                max-height: 92vh;

                overflow-y: auto;

                background: #ffffff;

                border-radius: 10px;

                padding: 22px;

                box-shadow:
                    0 10px 40px
                    rgba(0,0,0,0.35);
            }


            .payslip-modal-actions {

                display: flex;

                justify-content: flex-end;

                gap: 10px;

                margin-bottom: 15px;
            }


            .payslip-action-button {

                border: 0;

                border-radius: 5px;

                padding: 10px 16px;

                cursor: pointer;

                color: #ffffff;

                font-weight: 600;
            }


            .payslip-print-button {

                background: #159447;
            }


            .payslip-close-button {

                background: #6c757d;
            }


            .payslip-document {

                background: #ffffff;

                color: #222222;

                padding: 25px;

                font-family:
                    Arial,
                    Helvetica,
                    sans-serif;
            }


            .payslip-header {

                text-align: center;

                color: #12395b;

                border-bottom:
                    2px solid #12395b;

                padding-bottom: 15px;

                margin-bottom: 20px;
            }


            .payslip-header h1 {

                margin:
                    0 0 8px;

                font-size: 24px;
            }


            .payslip-header h2 {

                margin: 0;

                font-size: 17px;

                color: #555555;
            }


            .payslip-details {

                display: grid;

                grid-template-columns:
                    1fr 1fr;

                gap: 15px;

                margin-bottom: 20px;
            }


            .payslip-detail {

                border:
                    1px solid #dddddd;

                padding: 14px;

                border-radius: 5px;
            }


            .payslip-detail strong {

                display: block;

                color: #12395b;

                margin-bottom: 5px;
            }


            .payslip-document-table {

                width: 100%;

                border-collapse:
                    collapse;
            }


            .payslip-document-table th {

                background: #12395b;

                color: white;

                text-align: left;

                padding: 10px;
            }


            .payslip-document-table td {

                padding: 11px;

                border-bottom:
                    1px solid #dddddd;
            }


            .payslip-document-table
            .amount {

                text-align: right;
            }


            .total-deduction-row {

                background: #fff4df;
            }


            .net-row {

                background: #eaf3fb;
            }


            .payslip-footer {

                text-align: center;

                color: #666666;

                margin-top: 25px;

                font-size: 13px;
            }


            .payslip-table-wrapper {

                overflow-x: auto;

                width: 100%;
            }


            .payslip-table {

                width: 100%;

                border-collapse:
                    collapse;
            }


            .payslip-table th {

                padding: 10px;

                background: #e8ebef;

                white-space: nowrap;
            }


            .payslip-table td {

                padding: 10px;

                white-space: nowrap;

                border-bottom:
                    1px solid #eeeeee;
            }


            .payslip-empty {

                padding: 15px;

                background: #f5f5f5;

                border-radius: 5px;

                color: #555555;
            }


            @media print {

                body * {

                    visibility:
                        hidden !important;
                }


                .payslip-document,
                .payslip-document * {

                    visibility:
                        visible !important;
                }


                .payslip-document {

                    position: absolute;

                    left: 0;

                    top: 0;

                    width: 100%;
                }


                .payslip-modal-actions {

                    display:
                        none !important;
                }
            }

        `;


        document.head.appendChild(style);
    }


    // =========================================================
    // CREATE VIEW MODAL
    // =========================================================

    function createViewModal() {

        let modal =
            document.getElementById(
                "payslipViewModal"
            );


        if (modal) {
            return modal;
        }


        modal =
            document.createElement("div");


        modal.id =
            "payslipViewModal";


        modal.className =
            "payslip-modal";


        modal.innerHTML = `

            <div class="payslip-modal-box">

                <div class="payslip-modal-actions">

                    <button
                        type="button"
                        id="payslipModalPrint"
                        class="
                            payslip-action-button
                            payslip-print-button
                        "
                    >
                        Print / Save PDF
                    </button>


                    <button
                        type="button"
                        id="payslipModalClose"
                        class="
                            payslip-action-button
                            payslip-close-button
                        "
                    >
                        Close
                    </button>

                </div>


                <div id="payslipModalContent">
                </div>

            </div>

        `;


        document.body.appendChild(modal);


        document
            .getElementById(
                "payslipModalClose"
            )
            .addEventListener(
                "click",
                closeView
            );


        document
            .getElementById(
                "payslipModalPrint"
            )
            .addEventListener(
                "click",
                function () {

                    const index =
                        Number(
                            modal.dataset
                                .payslipIndex
                        );

                    printPayslip(index);
                }
            );


        modal.addEventListener(
            "click",
            function (event) {

                if (
                    event.target === modal
                ) {

                    closeView();
                }
            }
        );


        return modal;
    }


    // =========================================================
    // VIEW PAYSLIP
    // =========================================================

    function viewPayslip(
        index,
        employeeName
    ) {

        const payslip =
            getPayslip(index);


        /*
         * IMPORTANT:
         * No "Payslip not found" alert.
         */

        if (!payslip) {

            console.error(
                "Payslip data unavailable:",
                index
            );

            return;
        }


        currentEmployeeName =
            resolveEmployeeName(
                employeeName
            );


        addStyles();


        const modal =
            createViewModal();


        const content =
            document.getElementById(
                "payslipModalContent"
            );


        if (!content) {
            return;
        }


        modal.dataset.payslipIndex =
            String(index);


        content.innerHTML =
            createPayslipHtml(
                payslip,
                currentEmployeeName
            );


        modal.classList.add("active");


        document.body.style.overflow =
            "hidden";
    }


    // =========================================================
    // CLOSE
    // =========================================================

    function closeView() {

        const modal =
            document.getElementById(
                "payslipViewModal"
            );


        if (modal) {

            modal.classList.remove(
                "active"
            );
        }


        document.body.style.overflow =
            "";
    }


    // =========================================================
    // PRINT / SAVE PDF
    // =========================================================

    function printPayslip(index) {

        const payslip =
            getPayslip(index);


        if (!payslip) {

            console.error(
                "Payslip data unavailable for PDF:",
                index
            );

            return;
        }


        const employeeName =
            resolveEmployeeName(
                currentEmployeeName
            );


        const printFrame =
            document.createElement(
                "iframe"
            );


        printFrame.style.position =
            "fixed";

        printFrame.style.right =
            "0";

        printFrame.style.bottom =
            "0";

        printFrame.style.width =
            "0";

        printFrame.style.height =
            "0";

        printFrame.style.border =
            "0";

        printFrame.setAttribute(
            "aria-hidden",
            "true"
        );


        document.body.appendChild(
            printFrame
        );


        const printDocument =
            printFrame.contentDocument ||
            printFrame.contentWindow.document;


        printDocument.open();


        printDocument.write(`

            <!DOCTYPE html>

            <html lang="en">

            <head>

                <meta charset="UTF-8">

                <title>
                    Payslip -
                    ${escapeHtml(
                        payslip.month
                    )}
                </title>

                <style>

                    @page {

                        size: A4;

                        margin: 15mm;
                    }


                    * {

                        box-sizing:
                            border-box;
                    }


                    body {

                        margin: 0;

                        padding: 0;

                        background: white;

                        color: #222222;

                        font-family:
                            Arial,
                            Helvetica,
                            sans-serif;
                    }


                    .payslip-document {

                        width: 100%;
                    }


                    .payslip-header {

                        text-align: center;

                        color: #12395b;

                        border-bottom:
                            2px solid #12395b;

                        padding-bottom: 15px;

                        margin-bottom: 20px;
                    }


                    .payslip-header h1 {

                        margin:
                            0 0 8px;

                        font-size: 24px;
                    }


                    .payslip-header h2 {

                        margin: 0;

                        font-size: 17px;

                        color: #555555;
                    }


                    .payslip-details {

                        display: grid;

                        grid-template-columns:
                            1fr 1fr;

                        gap: 15px;

                        margin-bottom: 20px;
                    }


                    .payslip-detail {

                        border:
                            1px solid #dddddd;

                        padding: 14px;
                    }


                    .payslip-detail strong {

                        display: block;

                        color: #12395b;

                        margin-bottom: 5px;
                    }


                    table {

                        width: 100%;

                        border-collapse:
                            collapse;
                    }


                    th {

                        background: #12395b;

                        color: white;

                        text-align: left;

                        padding: 10px;
                    }


                    td {

                        padding: 11px;

                        border-bottom:
                            1px solid #dddddd;
                    }


                    .amount {

                        text-align: right;
                    }


                    .total-deduction-row {

                        background:
                            #fff4df;
                    }


                    .net-row {

                        background:
                            #eaf3fb;
                    }


                    .payslip-footer {

                        text-align: center;

                        color: #666666;

                        margin-top: 25px;

                        font-size: 13px;
                    }

                </style>

            </head>


            <body>

                ${createPayslipHtml(
                    payslip,
                    employeeName
                )}

            </body>

            </html>

        `);


        printDocument.close();


        setTimeout(
            function () {

                try {

                    printFrame
                        .contentWindow
                        .focus();

                    printFrame
                        .contentWindow
                        .print();

                } finally {

                    setTimeout(
                        function () {

                            printFrame.remove();

                        },
                        1000
                    );
                }

            },
            500
        );
    }


    // =========================================================
    // PDF BUTTON
    // =========================================================

    function downloadPayslipPDF(index) {

        printPayslip(index);
    }


    // =========================================================
    // RENDER PAYSLIPS
    // =========================================================

    function renderPayslips(
        payslips,
        employeeName = "Employee"
    ) {

        currentEmployeeName =
            resolveEmployeeName(
                employeeName
            );


        setPayslips(
            payslips
        );


        if (
            currentPayslips.length === 0
        ) {

            return `

                <div class="payslip-empty">

                    <p>
                        No payslips available.
                    </p>

                </div>

            `;
        }


        return `

            <div
                class="payslip-table-wrapper"
            >

                <table
                    class="payslip-table"
                >

                    <thead>

                        <tr>

                            <th>
                                Month
                            </th>

                            <th>
                                Gross Salary
                            </th>

                            <th>
                                Provident Fund
                            </th>

                            <th>
                                Insurance
                            </th>

                            <th>
                                Other Deduction
                            </th>

                            <th>
                                Total Deductions
                            </th>

                            <th>
                                Net Salary
                            </th>

                            <th>
                                Actions
                            </th>

                        </tr>

                    </thead>


                    <tbody>

                        ${currentPayslips
                            .map(
                                function (
                                    payslip,
                                    index
                                ) {

                                    return `

                                        <tr>

                                            <td>
                                                ${escapeHtml(
                                                    payslip.month
                                                )}
                                            </td>


                                            <td>
                                                ₹${formatAmount(
                                                    payslip.gross_salary
                                                )}
                                            </td>


                                            <td>
                                                ₹${formatAmount(
                                                    payslip.provident_fund
                                                )}
                                            </td>


                                            <td>
                                                ₹${formatAmount(
                                                    payslip.insurance
                                                )}
                                            </td>


                                            <td>
                                                ₹${formatAmount(
                                                    payslip.other_deduction
                                                )}
                                            </td>


                                            <td>
                                                ₹${formatAmount(
                                                    payslip.deductions
                                                )}
                                            </td>


                                            <td>

                                                <strong>
                                                    ₹${formatAmount(
                                                        payslip.net_salary
                                                    )}
                                                </strong>

                                            </td>


                                            <td>

                                                <div
                                                    style="
                                                        display:flex;
                                                        gap:6px;
                                                        flex-wrap:wrap;
                                                    "
                                                >

                                                    <button
                                                        type="button"
                                                        class="
                                                            btn-primary
                                                            payslip-view-button
                                                        "
                                                        data-payslip-index="${index}"
                                                    >
                                                        View
                                                    </button>


                                                    <button
                                                        type="button"
                                                        class="
                                                            btn-success
                                                            payslip-pdf-button
                                                        "
                                                        data-payslip-index="${index}"
                                                    >
                                                        PDF
                                                    </button>

                                                </div>

                                            </td>

                                        </tr>

                                    `;
                                }
                            )
                            .join("")}

                    </tbody>

                </table>

            </div>

        `;
    }


    // =========================================================
    // BUTTON EVENTS
    // =========================================================

    document.addEventListener(
        "click",
        function (event) {

            const viewButton =
                event.target.closest(
                    ".payslip-view-button"
                );


            if (viewButton) {

                event.preventDefault();


                const index =
                    Number(
                        viewButton.dataset
                            .payslipIndex
                    );


                viewPayslip(
                    index,
                    currentEmployeeName
                );


                return;
            }


            const pdfButton =
                event.target.closest(
                    ".payslip-pdf-button"
                );


            if (pdfButton) {

                event.preventDefault();


                const index =
                    Number(
                        pdfButton.dataset
                            .payslipIndex
                    );


                downloadPayslipPDF(
                    index
                );
            }

        }
    );


    // =========================================================
    // EXPOSE MODULE
    // =========================================================

    window.PayslipsModule = {

        setPayslips,

        renderPayslips,

        formatAmount,

        viewPayslip,

        downloadPayslipPDF,

        printPayslip

    };


})();