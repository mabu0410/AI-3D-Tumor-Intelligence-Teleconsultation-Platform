import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, Text, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    hospital_id: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cases: Mapped[list["Case"]] = relationship("Case", back_populates="patient")
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="patient")


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    dicom_path: Mapped[str] = mapped_column(String(512), nullable=False)
    scan_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    scan_type: Mapped[str] = mapped_column(String(20), default="CT")  # CT | MRI
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="cases")
    segmentation_result: Mapped["SegmentationResult"] = relationship("SegmentationResult", back_populates="case", uselist=False)
    reconstruction_result: Mapped["ReconstructionResult"] = relationship("ReconstructionResult", back_populates="case", uselist=False)
    feature_result: Mapped["FeatureResult"] = relationship("FeatureResult", back_populates="case", uselist=False)
    classification_result: Mapped["ClassificationResult"] = relationship("ClassificationResult", back_populates="case", uselist=False)
    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="case", uselist=False)


class SegmentationResult(Base):
    __tablename__ = "segmentation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    mask_path: Mapped[str] = mapped_column(String(512), nullable=True)
    dice_score: Mapped[float] = mapped_column(Float, nullable=True)
    iou_score: Mapped[float] = mapped_column(Float, nullable=True)
    hausdorff_distance: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["Case"] = relationship("Case", back_populates="segmentation_result")


class ReconstructionResult(Base):
    __tablename__ = "reconstruction_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    mesh_path: Mapped[str] = mapped_column(String(512), nullable=True)
    volume_mm3: Mapped[float] = mapped_column(Float, nullable=True)
    surface_area_mm2: Mapped[float] = mapped_column(Float, nullable=True)
    sphericity: Mapped[float] = mapped_column(Float, nullable=True)
    roughness_index: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["Case"] = relationship("Case", back_populates="reconstruction_result")


class FeatureResult(Base):
    __tablename__ = "feature_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    feature_vector: Mapped[dict] = mapped_column(JSON, nullable=True)
    radiomics_features: Mapped[dict] = mapped_column(JSON, nullable=True)
    fractal_dimension: Mapped[float] = mapped_column(Float, nullable=True)
    surface_irregularity: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["Case"] = relationship("Case", back_populates="feature_result")


class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=True)  # benign | malignant
    malignancy_probability: Mapped[float] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    model_used: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["Case"] = relationship("Case", back_populates="classification_result")


class ProgressionPrediction(Base):
    __tablename__ = "progression_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    volume_change_3m: Mapped[float] = mapped_column(Float, nullable=True)   # % change in 3 months
    volume_change_6m: Mapped[float] = mapped_column(Float, nullable=True)   # % change in 6 months
    malignancy_risk_3m: Mapped[float] = mapped_column(Float, nullable=True)
    malignancy_risk_6m: Mapped[float] = mapped_column(Float, nullable=True)
    invasion_speed: Mapped[str] = mapped_column(String(20), nullable=True)  # fast | medium | slow
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    requesting_hospital: Mapped[str] = mapped_column(String(255), nullable=True)
    specialist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | in_review | completed
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    annotations: Mapped[dict] = mapped_column(JSON, nullable=True)
    signed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["Case"] = relationship("Case", back_populates="consultation")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_channel: Mapped[str] = mapped_column(String(20), default="sms")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="schedules")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="doctor")  # admin | doctor | specialist | patient
    hospital: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
