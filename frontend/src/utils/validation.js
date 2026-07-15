/**
 * Valida el formulario de registro de un estudiante.
 * @param {Object} f - Datos del formulario.
 * @returns {Object} Objeto con los errores encontrados por campo.
 */
export function validateStudentForm(f) {
  const errors = {};
  if (!f.full_name.trim()) {
    errors.full_name = "El nombre completo es obligatorio.";
  } else if (f.full_name.trim().length > 100) {
    errors.full_name = "El nombre completo no puede exceder los 100 caracteres.";
  }

  if (!f.document_id.trim()) {
    errors.document_id = "El documento es obligatorio.";
  } else if (!/^\d{6,15}$/.test(f.document_id.trim())) {
    errors.document_id = "Debe tener entre 6 y 15 digitos numericos.";
  }

  if (f.email.trim()) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.trim())) {
      errors.email = "Ingresa un email valido.";
    } else if (f.email.trim().length > 100) {
      errors.email = "El email no puede exceder los 100 caracteres.";
    }
  }

  if (!f.school_id.trim()) {
    errors.school_id = "El colegio es obligatorio.";
  } else if (f.school_id.trim().length > 50) {
    errors.school_id = "El ID del colegio no puede exceder los 50 caracteres.";
  }

  if (!f.grade.trim()) {
    errors.grade = "El grado es obligatorio.";
  } else if (f.grade.trim().length > 50) {
    errors.grade = "El grado no puede exceder los 50 caracteres.";
  }

  return errors;
}
