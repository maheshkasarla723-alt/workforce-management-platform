/* ============================================================
   ADMIN EMPLOYEE PROFILE + PAYSLIP
   ============================================================ */

(function () {

    "use strict";

    let adminEmployees = [];


    /* =========================================================
       BASIC HELPERS
       ========================================================= */

    function escapeHtml(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    function formatSalary(value) {

        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "₹0.00";
        }

        return `₹${number.toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`;

    }


    function getPayslips(employee) {

        const metadata =
            employee &&
            employee.profile_metadata &&
            typeof employee.profile_metadata === "object"
                ? employee.profile_metadata
                : {};

        if (Array.isArray(metadata.payslips)) {
            return metadata.payslips;
        }

        return [];

    }


    function getEmployeeName(employee) {

        if (!employee) {
            return "Employee";
        }

        return (
            employee.name ||
            employee.username ||
            employee.email ||
            "Employee"
        );

    }


    function getDepartmentName(employee) {

        if (
            employee &&
            employee.department &&
            employee.department.name
        ) {
            return employee.department.name;
        }

        return "Not Assigned";

    }


    function getManagerName(employee) {

        if (
            employee &&
            employee.manager_name
        ) {
            return employee.manager_name;
        }

        if (
            typeof window.getEmployeeName === "function" &&
            employee &&
            employee.manager_id
        ) {
            return window.getEmployeeName(
                employee.manager_id
            );
        }

        return "No Manager";

    }


    /* =========================================================
       FIND EMPLOYEE
       ========================================================= */

    function findEmployee(employeeId) {

        return (
            adminEmployees.find(
                item =>
                    Number(item.id) === Number(employeeId)
            ) || null
        );

    }


    /* =========================================================
       VIEW EMPLOYEE PAYSLIPS
       ========================================================= */

    function viewEmployeePayslip(employeeId) {

        const employee = findEmployee(employeeId);

        if (!employee) {

            alert(
                "Employee not found. Please reload the Employee Management page."
            );

            return;
        }


        const payslips = getPayslips(employee);


        if (!payslips || payslips.length === 0) {

            alert(
                `No payslip is available for ${getEmployeeName(employee)}.`
            );

            return;
        }


        if (
            !window.PayslipsModule ||
            typeof window.PayslipsModule.renderPayslips !== "function"
        ) {

            alert(
                "Payslip module is not loaded. Please refresh the page and try again."
            );

            return;
        }


        /*
         * IMPORTANT:
         *
         * Do NOT automatically open the current month.
         *
         * First display ALL monthly payslips.
         *
         * The user can then click View for the
         * exact month they want.
         */

        showEmployeePayslipList(
            employee,
            payslips
        );

    }


    /* =========================================================
       SHOW ALL MONTHLY PAYSLIPS
       ========================================================= */

    function showEmployeePayslipList(
        employee,
        payslips
    ) {

        let modal =
            document.getElementById(
                "adminPayslipListModal"
            );


        /*
         * Create the modal only once.
         */

        if (!modal) {

            modal =
                document.createElement("div");

            modal.id =
                "adminPayslipListModal";

            modal.className =
                "modal";


            modal.innerHTML = `

                <div
                    class="modal-content"
                    style="
                        max-width:1000px;
                        width:95%;
                    "
                >

                    <div class="modal-header">

                        <h3
                            id="adminPayslipListTitle"
                        >
                            Employee Payslips
                        </h3>

                        <span
                            class="close"
                            id="adminPayslipListClose"
                        >
                            &times;
                        </span>

                    </div>


                    <div
                        id="adminPayslipListContent"
                    ></div>


                    <div
                        class="form-actions"
                        style="
                            margin-top:20px;
                        "
                    >

                        <button
                            type="button"
                            class="btn-secondary"
                            id="adminPayslipListCloseButton"
                        >
                            Close
                        </button>

                    </div>

                </div>

            `;


            document.body.appendChild(
                modal
            );


            const closeButton =
                document.getElementById(
                    "adminPayslipListClose"
                );

            if (closeButton) {

                closeButton.onclick =
                    closeEmployeePayslipList;

            }


            const closeButtonBottom =
                document.getElementById(
                    "adminPayslipListCloseButton"
                );

            if (closeButtonBottom) {

                closeButtonBottom.onclick =
                    closeEmployeePayslipList;

            }


            /*
             * Close when clicking outside modal.
             */

            modal.addEventListener(
                "click",
                function (event) {

                    if (
                        event.target === modal
                    ) {

                        closeEmployeePayslipList();

                    }

                }
            );

        }


        /*
         * Set employee name in title.
         */

        const title =
            document.getElementById(
                "adminPayslipListTitle"
            );

        if (title) {

            title.textContent =
                `${getEmployeeName(employee)} - Payslips`;

        }


        /*
         * Find payslip container.
         */

        const container =
            document.getElementById(
                "adminPayslipListContent"
            );


        if (!container) {

            alert(
                "Unable to display payslips."
            );

            return;
        }


        /*
         * Make sure the existing PayslipsModule
         * has the employee's payslips.
         */

        if (
            typeof window.PayslipsModule.setPayslips ===
            "function"
        ) {

            window.PayslipsModule.setPayslips(
                payslips
            );

        }


        /*
         * IMPORTANT:
         *
         * renderPayslips() creates the monthly table.
         *
         * Each row has its own View button.
         *
         * When the user clicks View on a particular
         * month, PayslipsModule.viewPayslip(index)
         * opens THAT exact payslip.
         */

        container.innerHTML =
            window.PayslipsModule.renderPayslips(
                payslips,
                getEmployeeName(employee)
            );


        /*
         * Show modal.
         */

        modal.style.display =
            "block";


        document.body.style.overflow =
            "hidden";

    }


    /* =========================================================
       CLOSE PAYSLIP LIST
       ========================================================= */

    function closeEmployeePayslipList() {

        const modal =
            document.getElementById(
                "adminPayslipListModal"
            );


        if (modal) {

            modal.style.display =
                "none";

        }


        document.body.style.overflow =
            "";

    }


    /* =========================================================
       EMPLOYEE PROFILE
       ========================================================= */

    function openEmployeeProfile(employeeId) {

        const employee =
            findEmployee(employeeId);


        if (!employee) {
            return;
        }


        /*
         * Keep Profile Metadata available
         * for the employee profile.
         *
         * Payslip data is NOT deleted here.
         */

        const metadata =
            employee.profile_metadata &&
            typeof employee.profile_metadata === "object"
                ? employee.profile_metadata
                : {};


        const jobRole =
            metadata.job_role ||
            "Not specified";


        const departmentName =
            getDepartmentName(employee);


        const managerName =
            getManagerName(employee);


        const profileContent = `

            <div class="profile-grid">


                <div class="profile-card">

                    <strong>
                        Employee ID
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            employee.id
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Name
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            getEmployeeName(employee)
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Email
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            employee.email || "-"
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Job Role
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            jobRole
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Salary
                    </strong>

                    <div class="profile-value">

                        ${formatSalary(
                            employee.salary
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Status
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            employee.status || "-"
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Department
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            departmentName
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Manager
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            managerName
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Joining Date
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            employee.joining_date || "-"
                        )}

                    </div>

                </div>


                <div class="profile-card">

                    <strong>
                        Skills
                    </strong>

                    <div class="profile-value">

                        ${escapeHtml(
                            employee.skills || "-"
                        )}

                    </div>

                </div>


            </div>


            <div
                style="
                    margin-top:25px;
                    padding:20px;
                    border:1px solid #ddd;
                    border-radius:10px;
                    background:#f8fafc;
                "
            >

                <h3
                    style="
                        color:#12395b;
                        margin-top:0;
                    "
                >
                    Payslip
                </h3>


                <p
                    style="
                        color:#555;
                        margin-bottom:15px;
                    "
                >
                    View the employee's payslip
                    without displaying payslip
                    data in the employee table.
                </p>


                <button
                    type="button"
                    class="btn-primary"
                    onclick="
                        EmployeeProfileModule.viewEmployeePayslip(
                            ${employee.id}
                        )
                    "
                >
                    View Payslip
                </button>


            </div>

        `;


        const title =
            document.getElementById(
                "employeeProfileTitle"
            );


        const content =
            document.getElementById(
                "employeeProfileContent"
            );


        if (title) {

            title.textContent =
                `${getEmployeeName(employee)} - Employee Profile`;

        }


        if (content) {

            content.innerHTML =
                profileContent;

        }


        /*
         * Existing Edit button.
         */

        const editButton =
            document.getElementById(
                "employeeProfileEditButton"
            );


        if (editButton) {

            editButton.onclick =
                function () {

                    /*
                     * Close profile first.
                     */

                    if (
                        typeof window.closeEmployeeProfile ===
                        "function"
                    ) {

                        window.closeEmployeeProfile();

                    }


                    /*
                     * Open existing employee edit.
                     */

                    if (
                        typeof window.editEmployee ===
                        "function"
                    ) {

                        window.editEmployee(
                            employee.id
                        );

                    }

                };

        }


        /*
         * Show profile modal.
         */

        const modal =
            document.getElementById(
                "employeeProfileModal"
            );


        if (modal) {

            modal.style.display =
                "block";

        }

    }


    /* =========================================================
       SET EMPLOYEES
       ========================================================= */

    function setEmployees(employeeList) {

        adminEmployees =
            Array.isArray(employeeList)
                ? employeeList
                : [];

    }


    /* =========================================================
       EXPOSE MODULE
       ========================================================= */

    window.EmployeeProfileModule = {

        setEmployees,

        openEmployeeProfile,

        viewEmployeePayslip,

        closeEmployeePayslipList

    };


    /*
     * Keep compatibility with existing:
     *
     * onclick="openEmployeeProfile(...)"
     */

    window.openEmployeeProfile =
        openEmployeeProfile;


})();