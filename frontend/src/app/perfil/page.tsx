"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/feedback/ToastProvider";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import {
  obtenerPerfilAdministrador,
  actualizarPerfilAdministrador,
  cambiarContrasena,
  obtenerProvincias,
  obtenerLocalidades,
  UserProfile,
  Provincia,
  Localidad,
} from "@/lib/api";

export default function PerfilPage() {
  const { token, logout } = useAuth();
  const router = useRouter();
  const { showToast } = useToast();
  
  const [loading, setLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [changePasswordMode, setChangePasswordMode] = useState(false);
  
  // Estados para edición de perfil
  const [nombreSupermercado, setNombreSupermercado] = useState("");
  const [provincia, setProvincia] = useState("");
  const [provinciaId, setProvinciaId] = useState(""); // ID de la provincia para el selector
  const [localidad, setLocalidad] = useState("");
  const [logo, setLogo] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  
  // Estados para provincias y localidades
  const [provincias, setProvincias] = useState<{ label: string; value: string }[]>([]);
  const [localidades, setLocalidades] = useState<{ label: string; value: string }[]>([]);
  
  // Estados para cambio de contraseña
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  const [saving, setSaving] = useState(false);

  // Cargar perfil del usuario
  useEffect(() => {
    if (!token) {
      router.replace("/login");
      return;
    }

    const userType = localStorage.getItem('user_type');
    if (userType !== 'supermercado') {
      router.replace("/empleado/dashboard");
      return;
    }

    cargarPerfil();
    cargarProvincias();
  }, [token, router]);

  const cargarPerfil = async () => {
    try {
      setLoading(true);
      if (!token) return;
      
      const perfil = await obtenerPerfilAdministrador(token);
      setUserProfile(perfil);
      setNombreSupermercado(perfil.nombre_supermercado);
      setProvincia(perfil.provincia);
      setLocalidad(perfil.localidad);
      
      if (perfil.logo) {
        // Construir URL completa del logo
        const logoUrl = perfil.logo.startsWith('http') 
          ? perfil.logo 
          : `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'}${perfil.logo}`;
        setLogoPreview(logoUrl);
      }
    } catch (error) {
      console.error('Error al cargar perfil:', error);
      showToast('Error al cargar perfil', 'error');
    } finally {
      setLoading(false);
    }
  };

  const cargarProvincias = async () => {
    try {
      const data = await obtenerProvincias();
      const provinciasData = data.provincias
        .map((p: Provincia) => ({ label: p.nombre, value: String(p.id), nombre: p.nombre }))
        .sort((a, b) => a.label.localeCompare(b.label));
      
      setProvincias(provinciasData);
      
      // Si ya hay una provincia seleccionada, encontrar su ID
      if (provincia && !provinciaId) {
        const provinciaActual = provinciasData.find((p: any) => p.nombre === provincia);
        if (provinciaActual) {
          setProvinciaId(provinciaActual.value);
        }
      }
    } catch (error) {
      console.error('Error al cargar provincias:', error);
    }
  };

  useEffect(() => {
    if (!provinciaId || !editMode) return;
    
    const cargarLocalidadesPorProvincia = async () => {
      try {
        const data = await obtenerLocalidades(provinciaId);
        const uniqueLocalidades = Array.from(
          new Map(data.localidades.map((l: Localidad) => [l.nombre, l])).values()
        );
        
        setLocalidades(
          uniqueLocalidades
            .map((l) => ({ label: l.nombre, value: String(l.nombre) }))
            .sort((a, b) => a.label.localeCompare(b.label))
        );
      } catch (error) {
        console.error('Error al cargar localidades:', error);
      }
    };

    cargarLocalidadesPorProvincia();
  }, [provinciaId, editMode]);

  // Efecto para sincronizar provincia cuando se activa editMode
  useEffect(() => {
    if (editMode && provincia && provincias.length > 0 && !provinciaId) {
      const provinciaActual = provincias.find((p: any) => 
        p.label === provincia || p.nombre === provincia
      );
      if (provinciaActual) {
        setProvinciaId(provinciaActual.value);
      }
    }
  }, [editMode, provincia, provincias, provinciaId]);

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validar tipo de archivo
      if (!file.type.match(/image\/(jpeg|jpg)/)) {
        showToast('El logo debe ser una imagen JPG o JPEG', 'error');
        return;
      }
      
      // Validar tamaño (máximo 1MB)
      if (file.size > 1 * 1024 * 1024) {
        showToast('El logo no puede ser mayor a 1MB', 'error');
        return;
      }
      
      setLogo(file);
      
      // Crear preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveProfile = async () => {
    if (!token) return;
    
    try {
      setSaving(true);
      
      const updateData: any = {};
      
      if (nombreSupermercado !== userProfile?.nombre_supermercado) {
        updateData.nombre_supermercado = nombreSupermercado;
      }
      if (provincia !== userProfile?.provincia) {
        updateData.provincia = provincia;
      }
      if (localidad !== userProfile?.localidad) {
        updateData.localidad = localidad;
      }
      if (logo) {
        updateData.logo = logo;
      }
      
      const response = await actualizarPerfilAdministrador(token, updateData);
      setUserProfile(response.user);
      setProvincia(response.user.provincia);
      setLocalidad(response.user.localidad);
      setLogo(null); // Limpiar el archivo temporal
      setEditMode(false);
      showToast('Perfil actualizado exitosamente', 'success');
      
      // Actualizar preview con la URL del servidor si hay logo
      if (response.user.logo) {
        const logoUrl = response.user.logo.startsWith('http') 
          ? response.user.logo 
          : `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'}${response.user.logo}`;
        setLogoPreview(logoUrl);
      }
    } catch (error) {
      console.error('Error al actualizar perfil:', error);
      showToast(
        error instanceof Error ? error.message : 'Error al actualizar perfil',
        'error'
      );
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    if (!userProfile) return;
    
    setNombreSupermercado(userProfile.nombre_supermercado);
    setProvincia(userProfile.provincia);
    setLocalidad(userProfile.localidad);
    setLogo(null);
    
    // Restaurar el logo preview con URL completa
    if (userProfile.logo) {
      const logoUrl = userProfile.logo.startsWith('http') 
        ? userProfile.logo 
        : `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'}${userProfile.logo}`;
      setLogoPreview(logoUrl);
    } else {
      setLogoPreview(null);
    }
    
    // Restablecer el ID de provincia
    const provinciaActual = provincias.find((p: any) => p.nombre === userProfile.provincia || p.label === userProfile.provincia);
    if (provinciaActual) {
      setProvinciaId(provinciaActual.value);
    }
    
    setEditMode(false);
  };

  const handleChangePassword = async () => {
    if (!token) return;
    
    if (newPassword !== confirmPassword) {
      showToast('Las contraseñas no coinciden', 'error');
      return;
    }
    
    try {
      setSaving(true);
      
      await cambiarContrasena(token, {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      
      setChangePasswordMode(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      
      showToast('Contraseña actualizada exitosamente', 'success');
    } catch (error) {
      console.error('Error al cambiar contraseña:', error);
      showToast(
        error instanceof Error ? error.message : 'Error al cambiar contraseña',
        'error'
      );
    } finally {
      setSaving(false);
    }
  };

  const handleCancelChangePassword = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setChangePasswordMode(false);
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <Container size="lg" className="py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-lightText">Cargando perfil...</p>
          </div>
        </Container>
      </ProtectedRoute>
    );
  }

  if (!userProfile) {
    return (
      <ProtectedRoute>
        <Container size="lg" className="py-8">
          <Card>
            <div className="text-center p-6">
              <p className="text-lightText">No se pudo cargar el perfil</p>
              <Button onClick={cargarPerfil} className="mt-4">
                Reintentar
              </Button>
            </div>
          </Card>
        </Container>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <Container size="lg" className="py-8">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-text mb-2">Mi Perfil</h1>
            <p className="text-lightText">
              Gestiona la información de tu supermercado
            </p>
          </div>

          {/* Información del perfil */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Columna izquierda - Logo y datos básicos */}
            <div className="lg:col-span-1">
              <Card>
                <div className="text-center p-6">
                  {/* Logo */}
                  <div className="mb-4">
                    {logoPreview ? (
                      <div className="relative inline-block">
                        <img
                          src={logoPreview}
                          alt="Logo del supermercado"
                          className="w-32 h-32 rounded-full object-cover mx-auto border-4 border-primary/20"
                        />
                        {editMode && (
                          <button
                            onClick={() => {
                              setLogo(null);
                              // Restaurar el logo original si existe
                              if (userProfile.logo) {
                                const logoUrl = userProfile.logo.startsWith('http') 
                                  ? userProfile.logo 
                                  : `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'}${userProfile.logo}`;
                                setLogoPreview(logoUrl);
                              } else {
                                setLogoPreview(null);
                              }
                            }}
                            className="absolute top-0 right-0 bg-red-500 text-white rounded-full p-2 hover:bg-red-600 transition-colors"
                            title="Eliminar logo"
                          >
                            
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center mx-auto text-white text-5xl">
                        
                      </div>
                    )}
                  </div>

                  {editMode && (
                    <div className="mb-4">
                      <label className="block">
                        <span className="sr-only">Cambiar logo</span>
                        <input
                          type="file"
                          accept="image/jpeg,image/jpg"
                          onChange={handleLogoChange}
                          className="block w-full text-sm text-gray-500
                            file:mr-4 file:py-2 file:px-4
                            file:rounded-md file:border-0
                            file:text-sm file:font-semibold
                            file:bg-primary file:text-white
                            hover:file:bg-primary/90
                            cursor-pointer"
                        />
                      </label>
                      <p className="text-xs text-lightText mt-1">
                        JPG o JPEG, máximo 1MB
                      </p>
                    </div>
                  )}

                  <h2 className="text-xl font-bold text-text mb-1">
                    {userProfile.nombre_supermercado}
                  </h2>
                  <p className="text-sm text-lightText mb-4">
                    {userProfile.email}
                  </p>

                  <div className="border-t pt-4">
                    <div className="text-sm">
                      <p className="text-lightText">Miembro desde</p>
                      <p className="font-semibold text-text">
                        {new Date(userProfile.fecha_registro).toLocaleDateString('es-AR', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Columna derecha - Información detallada */}
            <div className="lg:col-span-2 space-y-6">
              {/* Información del supermercado */}
              <Card>
                <div className="p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold text-text">
                      Información del Supermercado
                    </h3>
                    {!editMode && !changePasswordMode && (
                      <Button
                        onClick={() => setEditMode(true)}
                        variant="outline"
                        size="sm"
                      >
                         Editar
                      </Button>
                    )}
                  </div>

                  <div className="space-y-4">
                    {editMode ? (
                      <>
                        <Input
                          label="Nombre del Supermercado"
                          value={nombreSupermercado}
                          onChange={(e) => setNombreSupermercado(e.target.value)}
                          required
                        />

                        <Select
                          label="Provincia"
                          value={provinciaId}
                          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                            const selectedId = e.target.value;
                            setProvinciaId(selectedId);
                            
                            // Encontrar el nombre de la provincia seleccionada
                            const selectedProvincia = provincias.find((p: any) => p.value === selectedId);
                            if (selectedProvincia) {
                              setProvincia(selectedProvincia.label);
                            }
                            
                            setLocalidad("");
                          }}
                          options={provincias}
                          required
                        />

                        <Select
                          label="Localidad"
                          value={localidad}
                          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setLocalidad(e.target.value)}
                          options={localidades}
                          required
                          disabled={!provinciaId}
                        />

                        <div className="flex gap-2 pt-4">
                          <Button
                            onClick={handleSaveProfile}
                            disabled={saving}
                            className="flex-1"
                          >
                            {saving ? 'Guardando...' : 'Guardar Cambios'}
                          </Button>
                          <Button
                            onClick={handleCancelEdit}
                            variant="outline"
                            disabled={saving}
                          >
                            Cancelar
                          </Button>
                        </div>
                      </>
                    ) : (
                      <>
                        <div>
                          <label className="text-sm font-medium text-lightText">
                            Nombre del Supermercado
                          </label>
                          <p className="text-text font-medium">
                            {userProfile.nombre_supermercado}
                          </p>
                        </div>

                        <div>
                          <label className="text-sm font-medium text-lightText">
                            CUIL
                          </label>
                          <p className="text-text font-medium">
                            {userProfile.cuil}
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium text-lightText">
                              Provincia
                            </label>
                            <p className="text-text font-medium">
                              {userProfile.provincia}
                            </p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-lightText">
                              Localidad
                            </label>
                            <p className="text-text font-medium">
                              {userProfile.localidad}
                            </p>
                          </div>
                        </div>

                        <div>
                          <label className="text-sm font-medium text-lightText">
                            Email
                          </label>
                          <p className="text-text font-medium">
                            {userProfile.email}
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </Card>

              {/* Cambio de contraseña */}
              <Card>
                <div className="p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold text-text">
                      Seguridad
                    </h3>
                    {!changePasswordMode && !editMode && (
                      <Button
                        onClick={() => setChangePasswordMode(true)}
                        variant="outline"
                        size="sm"
                      >
                         Cambiar Contraseña
                      </Button>
                    )}
                  </div>

                  {changePasswordMode ? (
                    <div className="space-y-4">
                      <Input
                        label="Contraseña Actual"
                        type="password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                      />

                      <Input
                        label="Nueva Contraseña"
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        helper="Mínimo 8 caracteres, debe incluir números y caracteres especiales"
                      />

                      <Input
                        label="Confirmar Nueva Contraseña"
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                      />

                      <div className="flex gap-2 pt-4">
                        <Button
                          onClick={handleChangePassword}
                          disabled={saving || !currentPassword || !newPassword || !confirmPassword}
                          className="flex-1"
                        >
                          {saving ? 'Cambiando...' : 'Cambiar Contraseña'}
                        </Button>
                        <Button
                          onClick={handleCancelChangePassword}
                          variant="outline"
                          disabled={saving}
                        >
                          Cancelar
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <p className="text-sm text-lightText">
                        Mantén tu cuenta segura cambiando tu contraseña regularmente.
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>
        </Container>
      </div>
    </ProtectedRoute>
  );
}
